# app/routes/payments.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from utils.order import create_order_util, verify_payment_util

router = APIRouter(prefix="/v1/payments", tags=["Payments"])

@router.post("/create-order/{product_id}")
def create_order(product_id: int, db: Session = Depends(get_db)):
    return create_order_util(product_id, db)


@router.post("/verify")
def verify_payment(order_id: str, payment_id: str, signature: str, db: Session = Depends(get_db)):
    return verify_payment_util(order_id, payment_id, signature)
