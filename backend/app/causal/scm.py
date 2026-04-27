"""
Causal Fairness SCM Module

Implements the Structural Causal Model for data generation and intervention.

References:
- Plečko & Bareinboim, "Causal Fairness Analysis: A Causal Toolkit for Fair Machine Learning," Foundations and Trends in Machine Learning 17(3):304-589, 2024.
- Plečko & Bareinboim, "Mind the Gap: A Causal Perspective on Bias Amplification in Prediction & Decision-Making," NeurIPS 2024.
"""

import networkx as nx
import pandas as pd
from typing import Dict, Callable, Optional


class StructuralCausalModel:
    def __init__(self, dag: nx.DiGraph, equations: Dict[str, Callable], noise: Dict[str, Callable]):
        if not nx.is_directed_acyclic_graph(dag):
            raise ValueError("The provided DAG is not acyclic.")
        
        self.dag = dag
        self.equations = equations
        self.noise = noise

    def sample(self, n: int, intervention: Optional[Dict[str, any]] = None) -> pd.DataFrame:
        """
        Samples data from the SCM.
        
        Args:
            n (int): Number of samples.
            intervention (dict, optional): Dictionary of nodes to intervene on and their values.
        """
        if intervention is None:
            intervention = {}
            
        # Get topological sort of the graph
        nodes_order = list(nx.topological_sort(self.dag))
        
        # Initialize dataframe
        df = pd.DataFrame(index=range(n))
        
        # Generate data in topological order
        for node in nodes_order:
            if node in intervention:
                val = intervention[node]
                # If the value is a callable, it's a dynamic intervention
                if callable(val):
                    df[node] = [val() for _ in range(n)]
                else:
                    df[node] = val
            else:
                # Get parents of the node
                parents = list(self.dag.predecessors(node))
                
                # Get noise
                if node in self.noise:
                    u = self.noise[node](n)
                else:
                    u = 0  # Deterministic if no noise specified
                    
                # Calculate value
                if node in self.equations:
                    if parents:
                        kwargs = {p: df[p].values for p in parents}
                        kwargs['u'] = u
                        df[node] = self.equations[node](**kwargs)
                    else:
                        df[node] = self.equations[node](u=u)
                else:
                    df[node] = u
                    
        return df

    def do(self, node: str, value: any) -> 'StructuralCausalModel':
        """
        Returns a new SCM with an intervened equation for the specified node.
        """
        new_dag = self.dag.copy()
        
        # Remove incoming edges to the intervened node
        incoming_edges = list(new_dag.in_edges(node))
        new_dag.remove_edges_from(incoming_edges)
        
        # Create new equations
        new_equations = self.equations.copy()
        new_equations[node] = lambda u, **kwargs: value if not callable(value) else value()
        
        return StructuralCausalModel(new_dag, new_equations, self.noise)
