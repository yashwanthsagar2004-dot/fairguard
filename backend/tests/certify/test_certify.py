import pytest
import os
from backend.app.certify.mc_cert import mc_cert
from backend.app.certify.pdf import generate_pdf
from backend.app.certify.verify_cli import verify_pdf
from shared.models import AccessLevel

def test_full_flow():
    audit_data = {
        "id": "test-123", "n_samples": 1000, "iia": 0.9, "accessLevel": AccessLevel.WB,
        "causal_results": {"ctfDE": {"point": 0.01}, "ctfIE": {"point": 0.01}, "ctfSE": {"point": 0.01}}
    }
    cert = mc_cert(audit_data)
    pdf = generate_pdf(cert)
    with open("test.pdf", "wb") as f: f.write(pdf)
    assert verify_pdf("test.pdf") is True
    
    # Tamper
    with open("test.pdf", "rb") as f: content = f.read()
    with open("test.pdf", "wb") as f: f.write(content.replace(b"CERTIFIED_FAIR", b"CERTIFIED_UNFAIR"))
    assert verify_pdf("test.pdf") is False
    os.remove("test.pdf")

def test_four_fifths():
    cert = mc_cert({"id": "fail", "impact_ratios": [0.7], "causal_results": {}})
    assert cert.verdict == "CERTIFIED_UNFAIR"
