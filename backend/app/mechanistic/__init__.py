"""
FairGuard Mechanistic Interpretability Module
=============================================

Local-only SAE-circuit audit for Gemma-2 models using Sparse Feature Circuits.

This module runs exclusively on local GPU hardware (RTX 4060 8GB minimum)
and is never deployed to Cloud Run. It provides white-box mechanistic
interpretability analysis via Sparse Autoencoders (SAEs) from Gemma Scope.

References:
    - Marks, Rager, Michaud, Belinkov, Bau, Mueller, "Sparse Feature Circuits:
      Discovering and Editing Interpretable Causal Graphs in Language Models,"
      ICLR 2025 Oral.
    - Lieberum et al., "Gemma Scope: Open Sparse Autoencoders Everywhere All At
      Once on Gemma 2," BlackboxNLP 2024.
    - Geiger et al., "Causal Abstraction: A Theoretical Foundation for
      Mechanistic Interpretability," JMLR 26(83):1-64, 2025.
    - Casper et al., "Black-Box Access is Insufficient for Rigorous AI Audits,"
      FAccT 2024, doi:10.1145/3630106.3659037.
"""

__all__ = [
    "sae_loader",
    "circuit",
    "shift",
    "iia",
    "server",
]
