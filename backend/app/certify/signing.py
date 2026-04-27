import hashlib
import os
import base64
from .certificate import Certificate

def sign_certificate(cert: Certificate) -> str:
    payload = cert.to_canonical_json().encode("utf-8")
    if os.getenv("FAIRGUARD_DEV_MODE", "1") == "1":
        return f"UNSIGNED — DEVELOPMENT ONLY — {hashlib.sha256(payload).hexdigest()[:16]}"
    
    kms_key = os.getenv("FAIRGUARD_KMS_KEY")
    if not kms_key:
        return f"UNSIGNED — KMS NOT CONFIGURED — {hashlib.sha256(payload).hexdigest()[:16]}"

    try:
        from google.cloud import kms
        client = kms.KeyManagementServiceClient()
        digest = hashlib.sha256(payload).digest()
        response = client.asymmetric_sign(
            request={"name": kms_key, "digest": {"sha256": digest}}
        )
        return base64.b64encode(response.signature).decode("utf-8")
    except Exception:
        return f"UNSIGNED — KMS ERROR — {hashlib.sha256(payload).hexdigest()[:16]}"
