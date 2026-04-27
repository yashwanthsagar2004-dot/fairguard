import math
from datetime import datetime
from .certificate import Certificate
from .signing import sign_certificate
from shared.models import AccessLevel

def mc_cert(audit_data: dict, alpha=0.05, delta=0.05, k=20) -> Certificate:
    """
    Implements MC-CERT algorithm: w = sqrt(log((9+k)/delta) / (2n)) + epsilon_phi
    """
    audit_id = audit_data.get("id", "unknown")
    n = audit_data.get("n_samples", 1000)
    iia = audit_data.get("iia", 0.85)
    access_level = audit_data.get("accessLevel", AccessLevel.BB)
    
    epsilon_phi = 1.0 - iia if access_level == AccessLevel.WB else 1.0
    w = math.sqrt(math.log((9 + k) / delta) / (2 * n)) + epsilon_phi
    
    causal_raw = audit_data.get("causal_results", {})
    causal_findings = {}
    min_impact_ratio = 1.0
    
    for layer in ["S", "D", "Y"]:
        causal_findings[layer] = {}
        for effect in ["DE", "IE", "SE"]:
            point = causal_raw.get(f"ctf{effect}", {}).get("point", 0.0)
            causal_findings[layer][effect] = (point, max(0, point - w), point + w)
            min_impact_ratio = min(min_impact_ratio, 1.0 - point)
            
    if "impact_ratios" in audit_data:
        min_impact_ratio = min(audit_data["impact_ratios"])
    
    verdict = "CERTIFIED_FAIR" if min_impact_ratio >= 0.8 else "CERTIFIED_UNFAIR"
    
    cert = Certificate(
        audit_id=audit_id, timestamp_utc=datetime.utcnow().isoformat(), access_level=access_level,
        stability_grade=audit_data.get("stability", {}).get("overall_grade", "N/A"),
        causal_effects=causal_findings, half_width=w, delta=delta, alpha=alpha, verdict=verdict,
        regulatory_mapping=[{"regulation": "NYC LL144", "status": "PASS" if min_impact_ratio >= 0.8 else "FAIL", "details": f"Ratio {min_impact_ratio:.2f}"},
                          {"regulation": "EU AI Act Art 9 & 15", "status": "PASS" if verdict == "CERTIFIED_FAIR" else "FAIL", "details": "Causal transparency."},
                          {"regulation": "Colorado SB21-169", "status": "PASS" if verdict == "CERTIFIED_FAIR" else "FAIL", "details": "Discrimination check."}],
        signature="", verification_url=f"https://fairguard.ai/verify/{audit_id}"
    )
    cert.signature = sign_certificate(cert)
    return cert
