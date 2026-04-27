import pytest
from unittest.mock import MagicMock, patch
from backend.app.report.gemini_report import generate_audit_report, AuditReport
from backend.app.certify.certificate import Certificate
from shared.models import AccessLevel

@pytest.fixture
def mock_cert():
    return Certificate(
        audit_id="test-audit",
        timestamp_utc="2026-04-28T00:00:00Z",
        access_level=AccessLevel.BB,
        stability_grade="A",
        causal_effects={"layer1": {"effect1": (0.05, 0.04, 0.06)}},
        half_width=0.01,
        delta=0.05,
        alpha=0.05,
        verdict="CERTIFIED_FAIR",
        regulatory_mapping=[],
        signature="SIG",
        verification_url="URL"
    )

@patch("backend.app.report.gemini_report.genai.Client")
def test_generate_report_fair(mock_genai, mock_cert):
    mock_client = mock_genai.return_value
    mock_client.models.generate_content.return_value.text = "## SECTION 1\nThe model is certified fair. It shows minimal direct bias. The causal drivers are stable. This audit confirms regulatory compliance.\n\n## SECTION 2\n- Ctf-DE: 0.05\n- Ctf-IE: 0.01\n- Ctf-SE: 0.02\n- TV: 0.08\n\n## SECTION 3\n| Regulation | Status | Justification |\n|------------|--------|---------------|\n| NYC LL144 | PASS | Compliant |\n| GDPR Art 22 | PASS | Compliant |\n| AI Act | PASS | Compliant |"
    
    with patch("backend.app.certify.certificate.Certificate.to_canonical_json", return_value='{"0.05":1, "0.01":1, "0.02":1, "0.08":1}'):
        report = generate_audit_report(mock_cert)
        assert "certified fair" in report.executive_summary.lower()
        assert len(report.causal_findings) == 4
        assert len(report.regulatory_mapping) == 3

@patch("backend.app.report.gemini_report.genai.Client")
def test_generate_report_unfair(mock_genai, mock_cert):
    mock_cert.verdict = "CERTIFIED_UNFAIR"
    mock_client = mock_genai.return_value
    mock_client.models.generate_content.return_value.text = "## SECTION 1\nThe model is certified unfair. Significant direct bias was detected. Causal effects exceed safety thresholds. Remediation is required immediately.\n\n## SECTION 2\n- Ctf-DE: 0.15\n- Ctf-IE: 0.05\n- Ctf-SE: 0.03\n- TV: 0.23\n\n## SECTION 3\n| Regulation | Status | Justification |\n|------------|--------|---------------|\n| NYC LL144 | FAIL | Significant bias |\n| GDPR Art 22 | FAIL | Non-compliant |\n| AI Act | PASS | Borderline |"
    
    with patch("backend.app.certify.certificate.Certificate.to_canonical_json", return_value='{"0.15":1, "0.05":1, "0.03":1, "0.23":1}'):
        report = generate_audit_report(mock_cert)
        assert any(row[1] == "FAIL" for row in report.regulatory_mapping)

@patch("backend.app.report.gemini_report.genai.Client")
def test_hallucination_retry(mock_genai, mock_cert):
    mock_client = mock_genai.return_value
    mock_client.models.generate_content.side_effect = [
        MagicMock(text="## SECTION 1\nThe model is fair. It shows minimal bias. The causal drivers are stable. This audit confirms compliance.\n\n## SECTION 2\n- Ctf-DE: 9.99\n- Ctf-IE: 0.01\n- Ctf-SE: 0.02\n- TV: 0.08\n\n## SECTION 3\n| Regulation | Status | Justification |\n| NYC LL144 | PASS | OK |\n| GDPR Art 22 | PASS | OK |\n| AI Act | PASS | OK |"),
        MagicMock(text="## SECTION 1\nThe model is fair. It shows minimal bias. The causal drivers are stable. This audit confirms compliance.\n\n## SECTION 2\n- Ctf-DE: 0.05\n- Ctf-IE: 0.01\n- Ctf-SE: 0.02\n- TV: 0.08\n\n## SECTION 3\n| Regulation | Status | Justification |\n|------------|--------|---------------|\n| NYC LL144 | PASS | OK |\n| GDPR Art 22 | PASS | OK |\n| AI Act | PASS | OK |")
    ]
    
    with patch("backend.app.certify.certificate.Certificate.to_canonical_json", return_value='{"0.05":1, "0.01":1, "0.02":1, "0.08":1}'):
        report = generate_audit_report(mock_cert)
        assert "9.99" not in str(report)
        assert "0.05" in str(report)
