from enum import Enum
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel

class AccessLevel(str, Enum):
    BB = "Black-Box"
    GB = "Grey-Box"
    WB = "White-Box"
    OB = "Open-Box"

class StabilityProfile(BaseModel):
    overall_grade: str
    per_family: Dict[str, float]

class CausalEffects(BaseModel):
    ctfDE: float
    ctfIE: float
    ctfSE: float
    totalVariation: float
    confidenceInterval: Tuple[float, float]

class DriftAlert(BaseModel):
    metric: str
    p_value: float
    threshold: float
    timestamp: str

class MechanisticPSE(BaseModel):
    circuitId: str
    activationScore: float
    isFair: bool

class Audit(BaseModel):
    id: str
    targetModel: str
    datasetName: str
    accessLevel: AccessLevel
    protectedAttributes: List[str]
    stability: StabilityProfile
    causal: CausalEffects
    drift_history: List[DriftAlert]
    mechanistic: Optional[List[MechanisticPSE]] = None
    modelId: Optional[str] = "gemini-2.0-flash"
    timestamp: str

class RegulatoryCompliance(BaseModel):
    regulation: str
    status: str # PASS / FAIL / INCONCLUSIVE
    justification: str

class Certificate(BaseModel):
    auditId: str
    verdict: str # CERTIFIED_FAIR / CERTIFIED_UNFAIR / INCONCLUSIVE
    overallStabilityGrade: str
    worstAffectedGroup: str
    disparityMagnitude: float
    remediationAction: str
    accessLevel: AccessLevel
    causalFindings: CausalEffects
    regulatoryCompliance: List[RegulatoryCompliance]
    modelId: Optional[str] = "gemini-2.0-flash"
    signature: str
    timestamp: str
