"""
SAE Loader — loads Gemma-2 base model + Gemma Scope JumpReLU SAE.

Fits within 8 GB VRAM on RTX 4060 via 4-bit NF4 quantization.
Falls back from Gemma-2-9B to Gemma-2-2B if VRAM is insufficient.

References:
    - Lieberum et al., "Gemma Scope: Open Sparse Autoencoders Everywhere All At
      Once on Gemma 2," BlackboxNLP 2024.
    - Casper et al., "Black-Box Access is Insufficient for Rigorous AI Audits,"
      FAccT 2024, doi:10.1145/3630106.3659037 — for access-level scoping.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional

import torch

logger = logging.getLogger(__name__)

# ----- Cache Configuration -----
CACHE_DIR = Path.home() / ".cache" / "fairguard" / "sae"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ----- Gemma Scope SAE release identifiers -----
_SAE_RELEASES = {
    "google/gemma-2-9b": "gemma-scope-9b-pt-res",
    "google/gemma-2-2b": "gemma-scope-2b-pt-res",
}

_DEFAULT_SAE_WIDTHS = {
    "google/gemma-2-9b": "width_16k/average_l0_71",
    "google/gemma-2-2b": "width_16k/average_l0_82",
}

# ----- Fallback Configuration -----
FALLBACK_MODEL = "google/gemma-2-2b"
FALLBACK_LAYER = 12
FALLBACK_REASON = "rtx_4060_vram_limit"


def _get_quantization_config():
    """4-bit NF4 quantization config for bitsandbytes."""
    from transformers import BitsAndBytesConfig

    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )


def _vram_available_mb() -> float:
    """Return free VRAM in MB, or 0 if no CUDA device."""
    if not torch.cuda.is_available():
        return 0.0
    free, _ = torch.cuda.mem_get_info()
    return free / (1024 * 1024)


def load_gemma_sae(
    model_id: str = "google/gemma-2-9b",
    layer: int = 20,
    force_cpu: bool = False,
) -> Tuple:
    """
    Load base model (4-bit quantized) and Gemma Scope JumpReLU SAE.

    Parameters
    ----------
    model_id : str
        HuggingFace model identifier. Default: ``"google/gemma-2-9b"``.
    layer : int
        Transformer layer for SAE hook point. Default: ``20``.
    force_cpu : bool
        Force CPU-only loading (for tests). Default: ``False``.

    Returns
    -------
    tuple
        ``(model, tokenizer, sae, metadata)`` where metadata is a dict
        containing ``base_model``, ``layer``, and optionally
        ``fallback_reason`` if the 9B model didn't fit.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer

    metadata = {"base_model": model_id, "layer": layer}
    actual_model_id = model_id
    actual_layer = layer

    # --- Attempt to load the requested model ---
    try:
        model, tokenizer = _load_model(actual_model_id, force_cpu)
    except (RuntimeError, torch.cuda.OutOfMemoryError) as e:
        if actual_model_id == FALLBACK_MODEL:
            raise  # Already at fallback, can't go smaller
        logger.warning(
            "Failed to load %s (%s). Falling back to %s at layer %d.",
            actual_model_id, e, FALLBACK_MODEL, FALLBACK_LAYER,
        )
        actual_model_id = FALLBACK_MODEL
        actual_layer = FALLBACK_LAYER
        metadata.update({
            "base_model": FALLBACK_MODEL,
            "layer": FALLBACK_LAYER,
            "fallback_reason": FALLBACK_REASON,
        })
        model, tokenizer = _load_model(actual_model_id, force_cpu)

    # --- Load SAE ---
    sae = _load_sae(actual_model_id, actual_layer, force_cpu)

    return model, tokenizer, sae, metadata


def _load_model(model_id: str, force_cpu: bool):
    """Load a HuggingFace model with 4-bit quantization or on CPU."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    logger.info("Loading model: %s (force_cpu=%s)", model_id, force_cpu)

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=str(CACHE_DIR),
        trust_remote_code=True,
    )

    if force_cpu:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            cache_dir=str(CACHE_DIR),
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True,
        )
    else:
        quant_config = _get_quantization_config()
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant_config,
            device_map="auto",
            cache_dir=str(CACHE_DIR),
            trust_remote_code=True,
        )

    model.eval()
    return model, tokenizer


def _load_sae(model_id: str, layer: int, force_cpu: bool):
    """
    Load the Gemma Scope JumpReLU SAE for a given model and layer.

    Uses sae-lens ``SAE.from_pretrained`` with the appropriate release
    and layer identifier.
    """
    from sae_lens import SAE

    release = _SAE_RELEASES.get(model_id)
    width_spec = _DEFAULT_SAE_WIDTHS.get(model_id, "width_16k/average_l0_71")

    if release is None:
        raise ValueError(
            f"No Gemma Scope SAE release known for model '{model_id}'. "
            f"Supported: {list(_SAE_RELEASES.keys())}"
        )

    sae_id = f"layer_{layer}/{width_spec}"
    logger.info("Loading SAE: release=%s, sae_id=%s", release, sae_id)

    device = "cpu" if force_cpu else "cuda"
    sae, cfg_dict, sparsity = SAE.from_pretrained(
        release=release,
        sae_id=sae_id,
        device=device,
    )
    sae.eval()

    return sae
