"""
Core stability audit orchestration for Rhea-style auditing.
Reference: Rhea et al., "An external stability audit framework to test the
validity of personality prediction in AI hiring," Data Min. Knowl. Discov.
36(6):2153-2193, 2022, DOI 10.1007/s10618-022-00861-0.
"""

import asyncio
import numpy as np
from typing import List, Callable, Any, Dict
from backend.app.stability.perturb import (
    format_perturbations,
    prompt_paraphrase,
    section_reorder,
    typo_injection,
    metadata_injection,
    temperature_repeats
)
from backend.app.stability.metrics import reliability_alpha
from shared.models import StabilityProfile

async def run_stability_audit(endpoint: Callable, benchmark: List[str]) -> StabilityProfile:
    """
    Run the stability audit against an endpoint using a benchmark dataset.
    Returns a StabilityProfile with per-family alphas and an overall grade.
    """
    
    # 1. Get original scores for benchmark
    original_scores = []
    for text in benchmark:
        score = await endpoint(text)
        original_scores.append(float(score))
    
    total_variance = np.var(original_scores) if original_scores else 0.0
    
    per_family_alphas = {}
    
    # Define families and their perturbation logic
    # Each family will produce a set of perturbed scores to compute variance
    
    families = {
        "format": lambda t: format_perturbations(t),
        "reorder": lambda t: section_reorder(t),
        "typo": lambda t: typo_injection(t),
        "metadata": lambda t: metadata_injection(t)
    }
    
    for name, perturb_fn in families.items():
        perturbed_variances = []
        for text in benchmark:
            # For each text, generate a few perturbations to get variance
            p_scores = []
            for _ in range(5):
                p_text = perturb_fn(text)
                p_score = await endpoint(p_text)
                p_scores.append(float(p_score))
            perturbed_variances.append(np.var(p_scores))
        
        per_family_alphas[name] = reliability_alpha(perturbed_variances, total_variance)
        
    # Paraphrase family (async)
    paraphrase_alphas = []
    for text in benchmark:
        rewrites = await prompt_paraphrase(text, n=5)
        p_scores = []
        for rw in rewrites:
            p_score = await endpoint(rw)
            p_scores.append(float(p_score))
        paraphrase_alphas.append(np.var(p_scores))
    per_family_alphas["paraphrase"] = reliability_alpha(paraphrase_alphas, total_variance)
    
    # Temperature family
    temp_alphas = []
    for text in benchmark:
        t_scores = await temperature_repeats(endpoint, text, n=10)
        temp_alphas.append(np.var(t_scores))
    per_family_alphas["temperature"] = reliability_alpha(temp_alphas, total_variance)
    
    # Grading logic
    alphas = list(per_family_alphas.values())
    min_alpha = min(alphas) if alphas else 0.0
    
    if all(a >= 0.9 for a in alphas):
        grade = "A"
    elif all(a >= 0.85 for a in alphas):
        grade = "B"
    elif all(a >= 0.75 for a in alphas):
        grade = "C"
    elif all(a >= 0.60 for a in alphas):
        grade = "D"
    else:
        grade = "F"
        
    return StabilityProfile(
        overall_grade=grade,
        per_family=per_family_alphas
    )
