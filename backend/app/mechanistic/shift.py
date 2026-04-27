"""
SAE Feature Ablation (Partial Shift).

Zeroes out specific SAE features to measure their causal effect on the
output logit.

References:
    - Marks et al., "Sparse Feature Circuits," ICLR 2025.
"""

import logging
from typing import List, Dict

import torch
from .circuit import _extract_residual_stream, _get_device

logger = logging.getLogger(__name__)

def shift_ablate(
    model, 
    tokenizer, 
    sae, 
    prompt: str, 
    feature_ids: List[int], 
    target_token: str
) -> Dict[str, float]:
    """
    Zeroes specified SAE feature columns in reconstruction, re-runs forward.
    
    Returns original logit, ablated logit, and the delta.
    """
    device = _get_device(model)
    
    # Tokenize target
    target_ids = tokenizer.encode(target_token, add_special_tokens=False)
    if not target_ids:
        target_ids = tokenizer.encode(" " + target_token, add_special_tokens=False)
    target_id = target_ids[0]

    # Get original residual
    layer = getattr(sae.cfg, "hook_layer", 20)
    _, residual = _extract_residual_stream(model, tokenizer, prompt, layer)
    r = residual[:, -1, :] # (1, d_model)

    with torch.no_grad():
        # 1. Original SAE reconstruction
        h = sae.encode(r)
        recon_orig = sae.decode(h)
        
        # 2. Ablated SAE reconstruction
        h_ablated = h.clone()
        for fid in feature_ids:
            if fid < h_ablated.shape[1]:
                h_ablated[0, fid] = 0.0
        recon_ablated = sae.decode(h_ablated)

        # 3. Project to logits
        def get_logit(hidden):
            if hasattr(model, "lm_head"):
                l = model.lm_head(hidden.to(device))
            else:
                l = torch.matmul(hidden.to(device), model.model.embed_tokens.weight.T)
            return l[0, target_id].item()

        orig_logit = get_logit(recon_orig)
        ablated_logit = get_logit(recon_ablated)

    return {
        "original_logit": float(orig_logit),
        "ablated_logit": float(ablated_logit),
        "delta": float(ablated_logit - orig_logit)
    }
