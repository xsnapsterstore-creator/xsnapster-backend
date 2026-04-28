from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from core.security import get_current_user
from schemas.coupon import ValidateCouponRequest, ValidateCouponResponse, CouponListItemResponse
from services.coupon_service import CouponService
from utils.order import OrderService
from services.delivery_charge_service import build_pricing_breakdown


router = APIRouter(prefix="/v1/coupons", tags=["Coupons"])


@router.post("/validate", response_model=ValidateCouponResponse)
def validate_coupon(
    payload: ValidateCouponRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[object, Depends(get_current_user)],
):
    # 1. Price the items exactly like order creation does
    priced_items, items_subtotal, _ = OrderService._validate_and_price_items(
        db, [item.dict() for item in payload.items]
    )

    # 2. Validate coupon eligibility
    coupon = CouponService.fetch_and_validate(db, payload.code, user.id)

    # 3. Compute discount
    discount_result = CouponService.compute_discount(coupon, priced_items)
    discount_amount = discount_result["discount_amount"]
    subtotal_after_coupon = round(max(items_subtotal - discount_amount, 0.0), 2)

    # 4. Compute delivery on discounted subtotal
    pricing = build_pricing_breakdown(
        subtotal=subtotal_after_coupon,
        policy=OrderService._get_delivery_policy(),
    )

    return ValidateCouponResponse(
        valid=True,
        code=coupon.code,
        rule_type=coupon.rule_type.value,
        percent_off=coupon.percent_off,
        required_qty=coupon.required_qty,
        free_qty=coupon.free_qty,
        matched_dimension=discount_result["matched_dimension"],
        items_subtotal=items_subtotal,
        coupon_discount_amount=discount_amount,
        subtotal_after_coupon=subtotal_after_coupon,
        delivery_charge=pricing["delivery_charge"],
        amount=pricing["amount"],
    )




@router.get("/", response_model=List[CouponListItemResponse])
def list_coupons(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[object, Depends(get_current_user)],
):
    return CouponService.list_eligible(db, user.id)