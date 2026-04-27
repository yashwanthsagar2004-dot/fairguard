"""
Test suite for mechanistic mPSE implementation.
Uses CPU-only mode with a tiny Gemma-2-2B stub for verification.
"""

import pytest
from unittest.mock import MagicMock
import torch

from backend.app.mechanistic.sae_loader import load_gemma_sae
from backend.app.mechanistic.circuit import mPSE

@pytest.fixture
def mock_sae_setup():
    """Mocks a tiny model and SAE for testing on CPU."""
    # Mocking model and tokenizer
    model = MagicMock()
    tokenizer = MagicMock()
    sae = MagicMock()
    
    # Mock tokenizer behavior
    tokenizer.encode.side_effect = lambda x, **kwargs: [101] # Dummy token id
    
    # Mock model device
    param = torch.nn.Parameter(torch.zeros(1))
    model.parameters.return_value = iter([param])
    
    # Mock residual extraction (dummy tensors)
    # Since we can't easily hook a Mock, we might need to patch the internal functions
    return model, tokenizer, sae

def test_mpse_returns_top_k(mock_sae_setup, monkeypatch):
    model, tokenizer, sae = mock_sae_setup
    
    # Patch internal extraction to return dummy data
    def mock_extract(m, t, p, l):
        return torch.tensor([[101]]), torch.randn(1, 10, 128) # seq_len=10, d_model=128
    
    monkeypatch.setattr("backend.app.mechanistic.circuit._extract_residual_stream", mock_extract)
    
    # Mock SAE behavior
    sae.encode.return_value = torch.randn(1, 100) # 100 features
    sae.decode.return_value = torch.randn(1, 128)
    sae.cfg.hook_layer = 12
    
    # Mock model head behavior
    model.lm_head.return_value = torch.randn(1, 1000) # vocab=1000
    
    # Run mPSE
    results = mPSE(
        model, tokenizer, sae,
        prompt_a0="Test A",
        prompt_a1="Test B",
        target_token="approve",
        top_k=20
    )
    
    assert isinstance(results, dict)
    assert len(results) == 20
    for k, v in results.items():
        assert isinstance(k, int)
        assert isinstance(v, float)
