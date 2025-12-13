from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.cart import CartItem
from typing import List, Literal


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    payment_id: str
    signature: str


class OrderItemSchema(BaseModel):
    product_id: int
    title: str
    image: Optional[str]
    ordered_price: float
    quantity: Optional[int] = 1
    dimension: str
    category: Optional[str]
    subcategory: Optional[str]

    class Config:
        orm_mode = True


class OrderSchema(BaseModel):
    id: int
    items: List[OrderItemSchema]
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
    address_id: int
    payment_method: Literal["COD", "RAZORPAY"]

