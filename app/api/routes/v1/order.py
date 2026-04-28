# app/routes/payments.py
from typing import Annotated
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
                 db: Annotated[Session, Depends(get_db)],
                 user: Annotated[object, Depends(get_current_user)]):
    return OrderService.create_order(
        db,
        user.id,
        [item.dict() for item in payload.items],
        address_id=payload.address_id,
        payment_method=payload.payment_method,
        idempotency_key=payload.idempotency_key,
        coupon_code=payload.coupon_code,
    )


@router.post("/verify-payment")
def verify_payment(
    payload: VerifyPaymentRequest,
    user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    return verify_payment_util(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
        order_id=payload.order_id,
        user_id=user.id,
        db=db,
    )


