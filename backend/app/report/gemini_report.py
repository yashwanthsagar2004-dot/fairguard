import os
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from google import genai
from .prompt_templates import AUDIT_REPORT_PROMPT_V1
from .validator import validate_report
from backend.app.certify.certificate import Certificate

@dataclass
class AuditReport:
    executive_summary: str
    causal_findings: List[str]
    regulatory_mapping: List[Tuple[str, str, str]]

def generate_audit_report(cert: Certificate) -> AuditReport:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    cert_json = cert.to_canonical_json()
    
    prompt = AUDIT_REPORT_PROMPT_V1.replace("{{cert_json}}", cert_json)
    
    def call_gemini(p):
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=p
        )
        return response.text

    output = call_gemini(prompt)
    report = parse_report(output)
    
    is_valid, violations = validate_report(report, cert)
    if not is_valid:
        retry_prompt = f"{prompt}\n\nYour previous output violated: {', '.join(violations)}. Regenerate."
        output = call_gemini(retry_prompt)
        report = parse_report(output)
        is_valid, violations = validate_report(report, cert)
        if not is_valid:
            # Static fallback
            return AuditReport(
                executive_summary="AI-generated report validation failed; using static template. The system detected inconsistencies in the generated report.",
                causal_findings=["DE: N/A", "IE: N/A", "SE: N/A", "TV: N/A"],
                regulatory_mapping=[("NYC LL144", "INCONCLUSIVE", "Validation failed"), ("GDPR Art 22", "INCONCLUSIVE", "Validation failed"), ("AI Act", "INCONCLUSIVE", "Validation failed")]
            )
            
    return report

def parse_report(text: str) -> AuditReport:
    # Use re.IGNORECASE and allow for optional colon or spaces after SECTION X
    sections = re.split(r'## SECTION \d:?', text, flags=re.IGNORECASE)
    
    exec_summary = sections[1].strip() if len(sections) > 1 else ""
    findings_raw = sections[2].strip() if len(sections) > 2 else ""
    mapping_raw = sections[3].strip() if len(sections) > 3 else ""
    
    # Clean up exec_summary from any remaining headers if split was partial
    exec_summary = re.sub(r'## .*', '', exec_summary).strip()
    
    causal_findings = [line.strip("- ").strip() for line in findings_raw.split('\n') if line.strip() and not line.startswith('##')]
    
    regulatory_mapping = []
    for line in mapping_raw.split('\n'):
        if '|' in line and not any(h in line for h in ['Regulation', '---']):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                regulatory_mapping.append((parts[0], parts[1], parts[2]))
                
    return AuditReport(exec_summary, causal_findings, regulatory_mapping)
