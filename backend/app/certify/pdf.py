import io
import qrcode
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from .certificate import Certificate

def generate_pdf(cert: Certificate) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"FairGuard MC-CERT: {cert.audit_id}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    summary = f"Audit verdict: {cert.verdict}. Stability: {cert.stability_grade}. "
    summary += "Confidence intervals calculated via Hoeffding bounds with mechanistic alignment correction."
    elements.append(Paragraph("Executive Summary", styles['Heading2']))
    elements.append(Paragraph(summary, styles['Normal']))

    elements.append(Paragraph("NYC LL144 Severity Table", styles['Heading2']))
    data = [["Attribute", "Layer", "Status"]]
    for layer in ["S", "D", "Y"]:
        status = "GREEN" if cert.verdict == "CERTIFIED_FAIR" else "RED"
        data.append(["Protected", layer, status])
    t = Table(data); t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t)
    elements.append(PageBreak())

    elements.append(Paragraph("Causal Findings", styles['Heading2']))
    for layer, effects in cert.causal_effects.items():
        for eff, vals in effects.items():
            elements.append(Paragraph(f"• Layer {layer} {eff}: {vals[0]:.4f} (CI: [{vals[1]:.4f}, {vals[2]:.4f}])", styles['Normal']))
    elements.append(PageBreak())

    elements.append(Paragraph("Regulatory Mapping", styles['Heading2']))
    reg_data = [["Regulation", "Status", "Details"]]
    for reg in cert.regulatory_mapping:
        reg_data.append([reg['regulation'], reg['status'], reg['details']])
    rt = Table(reg_data); rt.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(rt)
    
    qr = qrcode.QRCode(box_size=10, border=5); qr.add_data(cert.verification_url); qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO(); img_qr.save(qr_buffer, format='PNG'); qr_buffer.seek(0)
    elements.append(Spacer(1, 24)); elements.append(Image(qr_buffer, width=100, height=100))
    
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(30, 30, f"Signature: {cert.signature[:40]}...")
        canvas.setAuthor("FairGuard")
        canvas.setSubject(f"CERT_JSON:{cert.to_canonical_json()}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
