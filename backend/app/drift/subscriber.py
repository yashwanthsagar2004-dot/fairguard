import base64
import json
import logging
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

PII_FIELDS = {"name", "ssn", "email", "phone", "address"}

@router.post("/subscriber")
async def receive_decision(request: Request):
    envelope = await request.json()
    if not envelope or "message" not in envelope:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")
    
    msg = envelope["message"]
    if "data" not in msg:
        raise HTTPException(status_code=400, detail="No data in message")
    
    try:
        data = json.loads(base64.b64decode(msg["data"]).decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to decode message: {e}")
        return {"status": "error"}

    for field in PII_FIELDS:
        if field in data or field in data.get("protected_attrs", {}):
            logger.warning(f"Rejected message with PII field: {field}")
            return {"status": "rejected"}

    logger.info(f"Received decision for audit {data.get('audit_id')}")
    return {"status": "success"}
