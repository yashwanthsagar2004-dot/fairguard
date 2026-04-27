"""
Causal Fairness Gemini DAG Elicitation Module

Uses Gemini to elicit DAG structures from text descriptions.
"""

import os
import json
import hashlib
import networkx as nx
from google import genai
from google.genai import types

def build_dag_from_json(data: dict) -> nx.DiGraph:
    dag = nx.DiGraph()
    dag.add_nodes_from(data.get("nodes", []))
    for edge in data.get("edges", []):
        if len(edge) == 2:
            dag.add_edge(edge[0], edge[1])
    return dag

def elicit_dag_from_description(description: str) -> nx.DiGraph:
    """
    Calls Gemini 2.5 Flash to generate a DAG from a text description.
    Caches the results to avoid redundant API calls.
    """
    cache_dir = ".cache/gemini_dag"
    os.makedirs(cache_dir, exist_ok=True)
    
    desc_hash = hashlib.sha256(description.encode('utf-8')).hexdigest()
    cache_path = os.path.join(cache_dir, f"{desc_hash}.json")
    
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            data = json.load(f)
            return build_dag_from_json(data)
            
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Given the following description of a causal system, generate a Directed Acyclic Graph (DAG).
    Return the result as a JSON object with 'nodes' and 'edges'.
    
    Description:
    {description}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "nodes": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "edges": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}}
                },
                "required": ["nodes", "edges"]
            }
        ),
    )
    
    result = json.loads(response.text)
    dag = build_dag_from_json(result)
    
    if not nx.is_directed_acyclic_graph(dag):
        raise ValueError("Generated graph is not acyclic.")
        
    with open(cache_path, 'w') as f:
        json.dump(result, f)
        
    return dag
