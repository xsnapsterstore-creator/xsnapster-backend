from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from schemas.cart import CartItem
from typing import List, Literal


CouponRuleTypeLiteral = Literal["PERCENT_CART", "BUY_N_GET_M_SAME_DIMENSION"]

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: int  


class AppliedCouponSummarySchema(BaseModel):
    id: Optional[int] = None
    code: str
    rule_type: CouponRuleTypeLiteral
    percent_off: Optional[float] = None
    required_qty: Optional[int] = None
    free_qty: Optional[int] = None
    matched_dimension: Optional[str] = None

    class Config:
        from_attributes = True


class CreateOrderItemResponseSchema(BaseModel):
    product_id: int
    quantity: int
    price: float
    dimension: str


class CreateOrderResponseSchema(BaseModel):
    order_id: int
    subtotal_before_coupon: Optional[float] = None
    coupon_discount_amount: Optional[float] = None
    subtotal_after_coupon: Optional[float] = None
    items_subtotal: float
    delivery_charge: float
    amount: float
    currency: str
    payment_method: Literal["COD", "RAZORPAY"]
    payment_status: str
    payment_gateway_order_id: Optional[str] = None
    applied_coupon: Optional[AppliedCouponSummarySchema] = None
    items: List[CreateOrderItemResponseSchema]




class OrderItemSchema(BaseModel):
    product_id: int
    title: str
    image: Optional[str] = None
    ordered_price: float
    quantity: Optional[int] = 1
    dimension: str
    category: Optional[str] = None
    subcategory: Optional[str] = None

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    items: List[OrderItemSchema]
    razorpay_order_id: Optional[str] = None
    subtotal_before_coupon: Optional[float] = None
    coupon_discount_amount: Optional[float] = None
    subtotal_after_coupon: Optional[float] = None
    items_subtotal: Optional[float] = None
    delivery_charge: Optional[float] = None
    amount: float
    status: str
    created_at: datetime
    total_items: int
    total_cost: float
    payment: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_method: Optional[str] = None
    applied_coupon: Optional[AppliedCouponSummarySchema] = None

    class Config:
        from_attributes = True


class CreateOrderRequest(BaseModel):
    items: List[CartItem]
    address_id: int
    payment_method: Literal["COD", "RAZORPAY"]
    idempotency_key: str
    coupon_code: Optional[str] = Field(default=None, max_length=64)


