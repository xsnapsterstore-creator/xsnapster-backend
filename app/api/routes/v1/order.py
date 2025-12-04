# app/routes/payments.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from utils.order import OrderService
from core.security import get_current_user
from schemas.order import CreateOrderRequest, VerifyPaymentRequest
from services.razorpay_service import RazorpayService


router = APIRouter(prefix="/v1/payments", tags=["Payments"])

@router.post("/create")
def create_order(payload: CreateOrderRequest,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    return OrderService.create_order(db, user.id, [item.dict() for item in payload.items])


@router.post("/verify-payment")
def verify_payment(payload: VerifyPaymentRequest, db: Session = Depends(get_db)):

    service = RazorpayService()

    return service.verify_payment(
        db=db,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
