from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from schemas.cart import CartItem
from datetime import datetime

CouponRuleTypeLiteral = Literal["PERCENT_CART", "BUY_N_GET_M_SAME_DIMENSION"]


class ValidateCouponRequest(BaseModel):
    code: str = Field(..., max_length=64)
    items: List[CartItem]


class ValidateCouponResponse(BaseModel):
    valid: bool
    code: str
    rule_type: CouponRuleTypeLiteral
    percent_off: Optional[float] = None
    required_qty: Optional[int] = None
    free_qty: Optional[int] = None
    matched_dimension: Optional[str] = None
    items_subtotal: float          # raw cart total before discount
    coupon_discount_amount: float
    subtotal_after_coupon: float
    delivery_charge: float
    amount: float                  # final amount after discount + delivery


class CouponListItemResponse(BaseModel):
    id: int
    code: str
    rule_type: CouponRuleTypeLiteral
    percent_off: Optional[float] = None
    required_qty: Optional[int] = None
    free_qty: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    class Config:
        from_attributes = True