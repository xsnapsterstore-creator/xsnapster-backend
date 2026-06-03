from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services.razorpay_service import razorpay_service
from services.shiprocket_service import (
    verify_shiprocket_webhook_signature,
    verify_shiprocket_webhook_token,
)
from core.config import settings
from utils.razorpay_webhook_handler import handle_razorpay_event
from utils.shiprocket_webhook_handler import handle_shiprocket_event
from fastapi import Request
import json

router = APIRouter(tags=["Webhooks"])


@router.post("/v1/razorpay/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        return {"status": "missing signature"}

    if not razorpay_service.verify_webhook_signature(payload, signature):
        return {"status": "invalid signature"}

    event = json.loads(payload.decode("utf-8"))

    handle_razorpay_event(event, db)

    return {"status": "ok"}


@router.post("/v1/shipr/webhook")
async def shiprocket_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    auth_header_name = settings.SHIPROCKET_WEBHOOK_AUTH_HEADER
    auth_header_value = request.headers.get(auth_header_name)

    signature_header_name = settings.SHIPROCKET_WEBHOOK_SIGNATURE_HEADER
    signature = request.headers.get(signature_header_name)

    if not auth_header_value and not signature:
        return {"status": "missing signature"}

    token_ok = verify_shiprocket_webhook_token(auth_header_value or "")
    signature_ok = verify_shiprocket_webhook_signature(payload, signature or "")

    if not token_ok and not signature_ok:
        return {"status": "invalid signature"}

    event = json.loads(payload.decode("utf-8"))
    handle_shiprocket_event(event, db)
    return {"status": "ok"}

