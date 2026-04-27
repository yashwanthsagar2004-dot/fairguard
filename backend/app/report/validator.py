import re
from typing import List, Tuple
from backend.app.certify.certificate import Certificate

def validate_report(report, cert: Certificate) -> Tuple[bool, List[str]]:
    violations = []
    cert_json = cert.to_canonical_json()
    
    # (a) exec_summary has exactly 4 sentences.
    # Count occurrences of sentence-ending punctuation
    sentence_count = len(re.findall(r'[^.!?]+[.!?]', report.executive_summary.strip()))
    if sentence_count != 4:
        violations.append(f"Executive summary must have exactly 4 sentences, found {sentence_count}.")
        
    # (b) causal_findings has 4 bullets (DE, IE, SE, TV).
    if len(report.causal_findings) != 4:
        violations.append(f"Causal findings must have exactly 4 bullets, found {len(report.causal_findings)}.")
    else:
        tags = ["DE", "IE", "SE", "TV"]
        for tag in tags:
            if not any(tag in f for f in report.causal_findings):
                violations.append(f"Missing {tag} in causal findings.")
                
    # (c) regulatory_mapping has 3 rows.
    if len(report.regulatory_mapping) != 3:
        violations.append(f"Regulatory mapping must have exactly 3 rows, found {len(report.regulatory_mapping)}.")
        
    # (d) every numeric value in report appears in cert JSON
    # Find all numbers (including decimals)
    numbers = re.findall(r'\d+\.\d+|\d+', str(report.executive_summary) + str(report.causal_findings))
    for num in numbers:
        # Ignore numbers that are part of standard strings like "SECTION 1" or "4 sentences"
        if num in ["1", "2", "3", "4"]: continue
        if num not in cert_json:
            violations.append(f"Hallucination detected: Numeric value {num} not found in certificate.")
            
    return (len(violations) == 0, violations)
