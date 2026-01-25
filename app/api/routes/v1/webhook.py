from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services.razorpay_service import razorpay_service
from utils.razorpay_webhook_handler import handle_razorpay_event
from fastapi import Request
import json

router = APIRouter(prefix="/v1/razorpay", tags=["Webhooks"])
@router.post("/webhook")
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

