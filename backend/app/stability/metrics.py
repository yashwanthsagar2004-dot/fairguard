"""
Stability metrics for Rhea-style external stability auditing.
Reference: Rhea et al., "An external stability audit framework to test the
validity of personality prediction in AI hiring," Data Min. Knowl. Discov.
36(6):2153-2193, 2022, DOI 10.1007/s10618-022-00861-0.
"""

import numpy as np
from scipy.stats import kendalltau, spearmanr
from typing import List

def kendall_tau(original: List[float], perturbed: List[float]) -> float:
    """Compute Kendall's Tau correlation coefficient."""
    if len(original) < 2: return 1.0
    tau, _ = kendalltau(original, perturbed)
    return float(tau) if not np.isnan(tau) else 0.0

def spearman_rho(original: List[float], perturbed: List[float]) -> float:
    """Compute Spearman's Rank correlation coefficient."""
    if len(original) < 2: return 1.0
    rho, _ = spearmanr(original, perturbed)
    return float(rho) if not np.isnan(rho) else 0.0

def rank_flip_rate(original: List[float], perturbed: List[float]) -> float:
    """
    Compute the rate of rank flips.
    A flip occurs if the relative order of two elements changes.
    """
    n = len(original)
    if n < 2: return 0.0
    
    flips = 0
    total_pairs = n * (n - 1) / 2
    
    for i in range(n):
        for j in range(i + 1, n):
            # Check if order reversed
            if (original[i] < original[j] and perturbed[i] > perturbed[j]) or \
               (original[i] > original[j] and perturbed[i] < perturbed[j]):
                flips += 1
                
    return flips / total_pairs

def reliability_alpha(perturbed_variances: List[float], total_variance: float) -> float:
    """
    Compute Cronbach's alpha-style reliability metric.
    alpha = 1 - (mean_variance_perturbed / total_variance)
    As per Rhea et al. 2022 framework adaptation.
    """
    if total_variance == 0:
        return 1.0 if np.mean(perturbed_variances) == 0 else 0.0
    
    avg_perturbed_var = np.mean(perturbed_variances)
    alpha = 1 - (avg_perturbed_var / total_variance)
    return max(0.0, min(1.0, float(alpha)))
