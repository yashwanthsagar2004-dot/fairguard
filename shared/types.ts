export enum AccessLevel {
  BB = 'Black-Box',
  GB = 'Grey-Box',
  WB = 'White-Box',
  OB = 'Open-Box'
}

export interface StabilityProfile {
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  perturbationScore: number;
  scenarioResults: Record<string, number>;
}

export interface CausalEffects {
  ctfDE: number; // Counterfactual Direct Effect
  ctfIE: number; // Counterfactual Indirect Effect
  ctfSE: number; // Counterfactual Spurious Effect
  totalVariation: number;
  confidenceInterval: [number, number];
}

export interface DriftAlert {
  metric: string;
  p_value: number;
  threshold: number;
  timestamp: string;
}

export interface MechanisticPSE {
  circuitId: string;
  activationScore: number;
  isFair: boolean;
}

export interface Audit {
  id: string;
  targetModel: string;
  datasetName: string;
  accessLevel: AccessLevel;
  protectedAttributes: string[];
  stability: StabilityProfile;
  causal: CausalEffects;
  drift_history: DriftAlert[];
  mechanistic?: MechanisticPSE[];
  timestamp: string;
}

export interface Certificate {
  auditId: string;
  verdict: 'CERTIFIED_FAIR' | 'CERTIFIED_UNFAIR' | 'INCONCLUSIVE';
  overallStabilityGrade: string;
  worstAffectedGroup: string;
  disparityMagnitude: number;
  remediationAction: string;
  accessLevel: AccessLevel;
  causalFindings: CausalEffects;
  regulatoryCompliance: {
    regulation: string;
    status: 'PASS' | 'FAIL' | 'INCONCLUSIVE';
    justification: string;
  }[];
  signature: string;
  timestamp: string;
}
