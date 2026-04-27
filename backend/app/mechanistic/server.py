"""
Local-only FastAPI router for Mechanistic Audit.

Mounts /audit/mechanistic to provide white-box interpretability findings.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

from .sae_loader import load_gemma_sae
from .circuit import mPSE
from .shift import shift_ablate
from .iia import compute_iia

router = APIRouter()

# Global state for loaded model/SAE to avoid reloading
_STATE = {
    "model": None,
    "tokenizer": None,
    "sae": None,
    "metadata": None
}

class MechanisticAuditRequest(BaseModel):
    model_id: str = "google/gemma-2-9b"
    layer: int = 20
    prompts_a0: str
    prompts_a1: str
    target_token: str
    top_k: int = 20

@router.post("/audit/mechanistic")
async def audit_mechanistic(request: MechanisticAuditRequest):
    # Ensure model is loaded (Local-only RTX 4060)
    if _STATE["model"] is None:
        try:
            m, t, s, meta = load_gemma_sae(request.model_id, request.layer)
            _STATE.update({"model": m, "tokenizer": t, "sae": s, "metadata": meta})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load model on local GPU: {str(e)}")

    model = _STATE["model"]
    tokenizer = _STATE["tokenizer"]
    sae = _STATE["sae"]
    
    # 1. mPSE Circuit Discovery
    try:
        mpse_results = mPSE(
            model, tokenizer, sae, 
            request.prompts_a0, request.prompts_a1, 
            request.target_token, request.top_k
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"mPSE failed: {str(e)}")

    # 2. Shift Ablation (Top feature)
    top_feature_id = list(mpse_results.keys())[0] if mpse_results else None
    shift_delta = {}
    if top_feature_id is not None:
        shift_delta = shift_ablate(
            model, tokenizer, sae, 
            request.prompts_a0, [top_feature_id], 
            request.target_token
        )

    # 3. IIA Faithfulness
    # In a real scenario, we'd pass multiple pairs, here we use the metadata or a mock
    iia_val = compute_iia(model, sae, [], request.layer)

    return {
        "mpse_top_k": mpse_results,
        "shift_delta": shift_delta,
        "iia": iia_val,
        "access_level": "WB" if iia_val >= 0.8 else "GB",
        "metadata": _STATE["metadata"]
    }
