"""
Tests for Rhea-style external stability audit gating.
Reference: Rhea et al., "An external stability audit framework to test the
validity of personality prediction in AI hiring," Data Min. Knowl. Discov.
36(6):2153-2193, 2022, DOI 10.1007/s10618-022-00861-0.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from shared.models import StabilityProfile
from backend.main import app

client = TestClient(app)

PAYLOAD = {"endpoint_url": "http://mock", "benchmark_texts": ["Sample text"]}


def test_deterministic_endpoint_grade_a():
    """Deterministic mock endpoint -> grade A."""
    profile = StabilityProfile(
        overall_grade="A",
        per_family={
            "format": 0.95, "reorder": 0.96, "typo": 0.97,
            "metadata": 0.94, "paraphrase": 0.93, "temperature": 0.92
        },
    )
    with patch("backend.main.run_stability_audit", new_callable=AsyncMock, return_value=profile):
        resp = client.post("/audit/causal", json=PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["stability"]["overall_grade"] == "A"
    assert "warnings" not in data


def test_random_endpoint_grade_f_returns_412():
    """Random-output mock endpoint -> grade F + HTTP 412."""
    profile = StabilityProfile(
        overall_grade="F",
        per_family={
            "format": 0.10, "reorder": 0.15, "typo": 0.05,
            "metadata": 0.12, "paraphrase": 0.08, "temperature": 0.04
        },
    )
    with patch("backend.main.run_stability_audit", new_callable=AsyncMock, return_value=profile):
        resp = client.post("/audit/causal", json=PAYLOAD)
    assert resp.status_code == 412
    detail = resp.json()["detail"]
    assert detail["error"] == "stability_grade_below_minimum"
    assert detail["grade"] == "F"
    assert "Rhea" in detail["message"]


def test_borderline_endpoint_grade_c_with_warnings():
    """Borderline endpoint (alpha ~0.77) -> grade C, 200 with warnings."""
    profile = StabilityProfile(
        overall_grade="C",
        per_family={
            "format": 0.77, "reorder": 0.78, "typo": 0.76,
            "metadata": 0.79, "paraphrase": 0.77, "temperature": 0.78
        },
    )
    with patch("backend.main.run_stability_audit", new_callable=AsyncMock, return_value=profile):
        resp = client.post("/audit/causal", json=PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["stability"]["overall_grade"] == "C"
    assert "stability_grade_C" in data["warnings"]
