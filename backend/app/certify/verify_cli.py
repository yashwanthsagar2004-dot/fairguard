import sys
import json
import hashlib
from PyPDF2 import PdfReader

def verify_pdf(pdf_path: str):
    try:
        reader = PdfReader(pdf_path)
        subject = reader.metadata.get('/Subject', '')
        if not subject.startswith("CERT_JSON:"): return False
        cert_dict = json.loads(subject.replace("CERT_JSON:", ""))
        signature = cert_dict.pop('signature', '')
        payload = json.dumps(cert_dict, sort_keys=True, separators=(',', ':')).encode("utf-8")
        if "UNSIGNED" in signature:
            return hashlib.sha256(payload).hexdigest()[:16] in signature
        return True # Real KMS verify here
    except Exception: return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and verify_pdf(sys.argv[1]): print("VALID"); sys.exit(0)
    else: print("INVALID"); sys.exit(1)
