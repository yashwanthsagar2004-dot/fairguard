"""
Sparse Feature Circuit Discovery via mPSE (mechanistic Partial Shift Effect).

Implements attribution-patching through SAE feature space to identify the
top-K causal features driving differential model behaviour between a pair
of demographically-varied prompts.

References:
    - Marks, Rager, Michaud, Belinkov, Bau, Mueller, "Sparse Feature Circuits:
      Discovering and Editing Interpretable Causal Graphs in Language Models,"
      ICLR 2025 Oral.
    - Lieberum et al., "Gemma Scope: Open Sparse Autoencoders Everywhere All At
      Once on Gemma 2," BlackboxNLP 2024.
    - Geiger et al., "Causal Abstraction: A Theoretical Foundation for
      Mechanistic Interpretability," JMLR 26(83):1-64, 2025.
"""

import logging
from typing import Dict, Optional, Tuple

import torch
import torch.nn.functional as F

# Reproducibility
torch.manual_seed(42)

logger = logging.getLogger(__name__)


def _get_device(model) -> torch.device:
    """Infer device from model parameters."""
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def _extract_residual_stream(
    model,
    tokenizer,
    prompt: str,
    layer: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Forward a prompt through the model and extract the residual-stream
    activation at the specified transformer layer.
    """
    device = _get_device(model)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    input_ids = inputs["input_ids"]

    residual_activation = {}

    def hook_fn(module, inp, out):
        # Gemma-2 layers return a tuple; residual is first element
        if isinstance(out, tuple):
            residual_activation["value"] = out[0].detach()
        else:
            residual_activation["value"] = out.detach()

    # Register hook on the target layer
    # Note: Accessing model layers depends on the specific model class
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        target_layer = model.model.layers[layer]
    else:
        # Fallback for other model structures if needed
        raise AttributeError("Model structure not recognized for layer hook.")
        
    handle = target_layer.register_forward_hook(hook_fn)

    with torch.no_grad():
        model(**inputs)

    handle.remove()
    return input_ids, residual_activation["value"]


def mPSE(
    model,
    tokenizer,
    sae,
    prompt_a0: str,
    prompt_a1: str,
    target_token: str,
    top_k: int = 20,
    layer: Optional[int] = None,
) -> Dict[int, float]:
    """
    Compute the mechanistic Partial Shift Effect (mPSE).

    Algorithm (Marks et al., 2025, §3.2 adapted for SAE features):
        1. Forward both prompts; cache residual-stream activations at SAE layer.
        2. Encode through JumpReLU SAE → h0, h1.
        3. For each active feature i, compute the linear attribution:
             attr_i = (∂ logit_target / ∂ feature_i) · (h1_i − h0_i)
           evaluated at h0 (clean-run gradients).
        4. Return top-K features ranked by |attr_i|.
    """
    device = _get_device(model)

    # Resolve target token ID
    target_ids = tokenizer.encode(target_token, add_special_tokens=False)
    if not target_ids:
        # Try with a space if not found (common in tokenizers)
        target_ids = tokenizer.encode(" " + target_token, add_special_tokens=False)
        if not target_ids:
            raise ValueError(f"Cannot tokenize target_token: '{target_token}'")
    target_id = target_ids[0]

    # Resolve SAE layer
    if layer is None:
        layer = getattr(sae.cfg, "hook_layer", 20)

    logger.info(
        "mPSE: layer=%d, target_token='%s' (id=%d), top_k=%d",
        layer, target_token, target_id, top_k,
    )

    # ---- Step (a): Forward both prompts, cache residual streams ----
    _, residual_a0 = _extract_residual_stream(model, tokenizer, prompt_a0, layer)
    _, residual_a1 = _extract_residual_stream(model, tokenizer, prompt_a1, layer)

    # Use last-position residuals
    r0 = residual_a0[:, -1, :]  # (1, d_model)
    r1 = residual_a1[:, -1, :]  # (1, d_model)

    # ---- Step (b): Encode through SAE ----
    with torch.no_grad():
        h0 = sae.encode(r0)  # (1, n_features)
        h1 = sae.encode(r1)  # (1, n_features)

    # ---- Step (c): Attribution-patching via gradient ----
    # We compute: attr_i = (∂ logit_target / ∂ h_i) · (h1_i − h0_i)
    # evaluated at h = h0.

    h0_grad = h0.clone().detach().requires_grad_(True)

    # Decode from SAE features back to residual space
    reconstructed = sae.decode(h0_grad)  # (1, d_model)

    # Project through LM head to get target logit
    # For Gemma-2, lm_head exists or we use embed_tokens transpose
    if hasattr(model, "lm_head"):
        logits = model.lm_head(reconstructed.to(device))
    else:
        # Tie weights if lm_head is missing
        logits = torch.matmul(
            reconstructed.to(device),
            model.model.embed_tokens.weight.T,
        )

    target_logit = logits[0, target_id]
    target_logit.backward()

    grad = h0_grad.grad[0]  # (n_features,)

    # Attribution = grad_i * (h1_i - h0_i)
    delta_h = (h1 - h0)[0]  # (n_features,)
    attribution = (grad * delta_h).detach().cpu()

    # ---- Step (d): Select top-K by |attribution| ----
    abs_attr = attribution.abs()
    topk_values, topk_indices = torch.topk(abs_attr, min(top_k, len(abs_attr)))

    result = {}
    for idx in topk_indices.tolist():
        result[int(idx)] = float(attribution[idx].item())

    # Sort result by absolute magnitude descending
    result = dict(sorted(result.items(), key=lambda x: abs(x[1]), reverse=True))

    return result
