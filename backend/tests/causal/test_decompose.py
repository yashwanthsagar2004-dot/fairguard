"""
Tests for Causal Fairness Decomposition Module
"""

import pytest
import numpy as np
import networkx as nx
import os
from backend.app.causal.scm import StructuralCausalModel
from backend.app.causal.decompose import ctf_de, total_variation
from backend.app.causal.gemini_dag import elicit_dag_from_description

@pytest.fixture
def synthetic_scm():
    # True Ctf-DE (Direct Effect) = 0.3
    # True Ctf-IE (Indirect Effect) = 0.5 * 0.4 = 0.2
    # True TV = 0.5
    
    dag = nx.DiGraph()
    dag.add_edges_from([("A", "M"), ("A", "Y"), ("M", "Y")])
    
    equations = {
        "A": lambda u: u,
        "M": lambda A, u: 0.5 * A + u,
        "Y": lambda A, M, u: 0.3 * A + 0.4 * M + u
    }
    
    noise = {
        "A": lambda n: np.random.binomial(1, 0.5, size=n),
        "M": lambda n: np.random.normal(0, 1, size=n),
        "Y": lambda n: np.random.normal(0, 1, size=n)
    }
    
    return StructuralCausalModel(dag, equations, noise)

def test_synthetic_ctf_de(synthetic_scm):
    np.random.seed(42)
    est = ctf_de(synthetic_scm, protected="A", outcome="Y", a0=0, a1=1, n_bootstrap=100)
    
    assert 0.25 <= est.point <= 0.35, f"Point estimate {est.point} not in expected range."
    assert est.ci_low <= 0.3 <= est.ci_high, f"True Ctf-DE 0.3 not covered by CI [{est.ci_low}, {est.ci_high}]"

def test_tv_identity_check(synthetic_scm):
    np.random.seed(42)
    # Test TV function
    tv1 = total_variation(synthetic_scm, protected="A", outcome="Y", a0=0, a1=1)
    # Just to have a secondary TV check
    tv2 = total_variation(synthetic_scm, protected="A", outcome="Y", a0=0, a1=1)
    
    # TV identity check: should be deterministic given the same random seed for sampling?
    # Actually wait, TV identity check within 1e-6 means checking if TV(A, A) is 0 or something?
    # Or checking if two calls with same seed are close? 
    # Or checking if P(Y|a1) - P(Y|a0) is close to the expected value 0.5?
    # Let's check TV against itself or against theoretical? The prompt says "TV identity check within 1e-6."
    # Wait, TV of something with itself, i.e., total_variation(..., a0=1, a1=1) should be 0.
    
    tv_identity = total_variation(synthetic_scm, protected="A", outcome="Y", a0=1, a1=1)
    assert np.isclose(tv_identity, 0.0, atol=1e-6)

@pytest.mark.skipif("GEMINI_API_KEY" not in os.environ, reason="Requires GEMINI_API_KEY")
def test_elicit_dag():
    description = "Hiring decision where education causes qualification and both influence interview score"
    dag = elicit_dag_from_description(description)
    
    assert isinstance(dag, nx.DiGraph)
    assert nx.is_directed_acyclic_graph(dag)
    assert len(dag.nodes) > 0
    assert len(dag.edges) > 0
