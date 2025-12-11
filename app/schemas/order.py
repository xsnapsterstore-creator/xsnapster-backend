from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.cart import CartItem
from typing import List


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    payment_id: str
    signature: str

class OrderSchema(BaseModel):
    id: int
    product_ids: List[int]
    razorpay_order_id: Optional[str]
    amount: float
    status: str
    created_at: datetime
    total_items: int
    total_cost: float
    payment: Optional[str]
    paid_amount: Optional[float]
    payment_method: Optional[str]

    class Config:
        orm_mode = True


class CreateOrderRequest(BaseModel):
    items: List[CartItem]

