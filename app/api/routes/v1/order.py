# app/routes/payments.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from utils.order import OrderService
from core.security import get_current_user
from schemas.order import CreateOrderRequest, VerifyPaymentRequest
from utils.payments import verify_payment_util
from fastapi import HTTPException, Request

router = APIRouter(prefix="/v1/payments", tags=["Payments"])

@router.post("/create")
def create_order(payload: CreateOrderRequest,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    return OrderService.create_order(db, user.id, [item.dict() for item in payload.items], address_id=payload.address_id, payment_method=payload.payment_method)


@router.post("/verify-payment")
def verify_payment(
    payload: VerifyPaymentRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return verify_payment_util(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
        user_id=user.id,
        db=db,
    )


