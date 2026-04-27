from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from shared.models import AccessLevel
import json

@dataclass
class Certificate:
    audit_id: str
    timestamp_utc: str
    access_level: AccessLevel
    stability_grade: str
    causal_effects: Dict[str, Dict[str, Tuple[float, float, float]]] # layer -> effect -> (point, low, high)
    mechanistic_pse: Optional[List[Dict]] = None
    half_width: float
    delta: float
    alpha: float
    verdict: str
    regulatory_mapping: List[Dict]
    signature: str
    verification_url: str
    
    def to_canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))
