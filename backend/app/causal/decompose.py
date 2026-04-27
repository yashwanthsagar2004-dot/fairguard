"""
Causal Fairness Decomposition Module

Computes Plečko-Bareinboim causal fairness decomposition (Ctf-DE, Ctf-IE, Ctf-SE, TV).

References:
- Plečko & Bareinboim, "Causal Fairness Analysis: A Causal Toolkit for Fair Machine Learning," Foundations and Trends in Machine Learning 17(3):304-589, 2024.
- Plečko & Bareinboim, "Mind the Gap: A Causal Perspective on Bias Amplification in Prediction & Decision-Making," NeurIPS 2024.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from dowhy import CausalModel
import networkx as nx

@dataclass
class EffectEstimate:
    point: float
    ci_low: float
    ci_high: float
    n_samples: int

def total_variation(scm, protected: str, outcome: str, a0, a1) -> float:
    """Computes Total Variation (TV) = E[Y | A=a1] - E[Y | A=a0]"""
    data = scm.sample(10000)
    mu1 = data[data[protected] == a1][outcome].mean()
    mu0 = data[data[protected] == a0][outcome].mean()
    return float(mu1 - mu0)

def _bootstrap_dowhy(data, protected, outcome, a0, a1, dag, estimand_type, n_bootstrap):
    gml_graph = "\n".join(nx.generate_gml(dag))
    
    model = CausalModel(
        data=data,
        treatment=protected,
        outcome=outcome,
        graph=gml_graph
    )
    
    try:
        estimand = model.identify_effect(estimand_type=estimand_type)
        if estimand_type in ["nonparametric-nde", "nonparametric-nie"]:
            if not estimand.get_mediator_variables():
                if estimand_type == "nonparametric-nie":
                    return EffectEstimate(0.0, 0.0, 0.0, n_bootstrap)
                else:
                    estimand = model.identify_effect(estimand_type="nonparametric-ate")
                    method_name = "backdoor.linear_regression"
            else:
                method_name = "mediation.two_stage_regression"
        else:
            method_name = "backdoor.linear_regression"
            
        estimate = model.estimate_effect(
            estimand,
            method_name=method_name,
            control_value=a0,
            treatment_value=a1,
            test_significance=False
        )
        point = estimate.value
    except Exception as e:
        print(f"Error in identification/estimation: {e}")
        return EffectEstimate(0.0, 0.0, 0.0, n_bootstrap)
        
    boot_estimates = []
    for _ in range(n_bootstrap):
        df_boot = data.sample(frac=1, replace=True)
        model_boot = CausalModel(
            data=df_boot,
            treatment=protected,
            outcome=outcome,
            graph=gml_graph
        )
        try:
            est_boot = model_boot.estimate_effect(
                estimand,
                method_name=method_name,
                control_value=a0,
                treatment_value=a1,
                test_significance=False
            )
            boot_estimates.append(est_boot.value)
        except:
            boot_estimates.append(point)
            
    ci_low = np.percentile(boot_estimates, 2.5)
    ci_high = np.percentile(boot_estimates, 97.5)
    return EffectEstimate(point=float(point), ci_low=float(ci_low), ci_high=float(ci_high), n_samples=n_bootstrap)

def ctf_de(scm, protected: str, outcome: str, a0, a1, n_bootstrap=1000) -> EffectEstimate:
    """Computes Counterfactual Direct Effect (Ctf-DE)"""
    data = scm.sample(10000)
    return _bootstrap_dowhy(data, protected, outcome, a0, a1, scm.dag, "nonparametric-nde", n_bootstrap)

def ctf_ie(scm, protected: str, outcome: str, a0, a1, n_bootstrap=1000) -> EffectEstimate:
    """Computes Counterfactual Indirect Effect (Ctf-IE)"""
    data = scm.sample(10000)
    return _bootstrap_dowhy(data, protected, outcome, a0, a1, scm.dag, "nonparametric-nie", n_bootstrap)

def ctf_se(scm, protected: str, outcome: str, a0, a1, n_bootstrap=1000) -> EffectEstimate:
    """Computes Counterfactual Spurious Effect (Ctf-SE)"""
    data = scm.sample(10000)
    gml_graph = "\n".join(nx.generate_gml(scm.dag))
    
    model = CausalModel(
        data=data,
        treatment=protected,
        outcome=outcome,
        graph=gml_graph
    )
    estimand = model.identify_effect(estimand_type="nonparametric-ate")
    method_name = "backdoor.linear_regression"
    
    def calc_se(df):
        tv = df[df[protected] == a1][outcome].mean() - df[df[protected] == a0][outcome].mean()
        model_b = CausalModel(data=df, treatment=protected, outcome=outcome, graph=gml_graph)
        try:
            ate_est = model_b.estimate_effect(estimand, method_name=method_name, control_value=a0, treatment_value=a1, test_significance=False).value
        except:
            ate_est = 0
        return tv - ate_est
        
    point = calc_se(data)
    boot_estimates = []
    for _ in range(n_bootstrap):
        df_boot = data.sample(frac=1, replace=True)
        try:
            boot_estimates.append(calc_se(df_boot))
        except:
            boot_estimates.append(point)
            
    ci_low = np.percentile(boot_estimates, 2.5)
    ci_high = np.percentile(boot_estimates, 97.5)
    
    return EffectEstimate(point=float(point), ci_low=float(ci_low), ci_high=float(ci_high), n_samples=n_bootstrap)
