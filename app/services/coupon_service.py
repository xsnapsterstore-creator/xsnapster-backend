from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.coupon import Coupon, CouponRuleType, CouponUsage


BXGY_ALLOWED_DIMENSIONS = {"A2", "A3", "A4"}


class CouponService:

    # --------------------------------------------------
    # 1. Fetch coupon + validate eligibility
    # --------------------------------------------------
    @staticmethod
    def fetch_and_validate(db: Session, code: str, user_id: str) -> Coupon:
        coupon = (
            db.query(Coupon)
            .filter(Coupon.code == code.strip().upper())
            .first()
        )

        if not coupon:
            raise HTTPException(400, f"Coupon '{code}' not found")

        if not coupon.is_active:
            raise HTTPException(400, "Coupon is inactive")

        now = datetime.now(timezone.utc)

        if coupon.starts_at and now < coupon.starts_at:
            raise HTTPException(400, "Coupon is not yet valid")

        if coupon.ends_at and now > coupon.ends_at:
            raise HTTPException(400, "Coupon has expired")

        # Global usage cap
        if coupon.max_total_uses is not None:
            total_used = db.query(CouponUsage).filter(
                CouponUsage.coupon_id == coupon.id
            ).count()
            if total_used >= coupon.max_total_uses:
                raise HTTPException(400, "Coupon usage limit reached")

        # Per-user usage cap
        if coupon.max_uses_per_user is not None:
            user_used = db.query(CouponUsage).filter(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id,
            ).count()
            if user_used >= coupon.max_uses_per_user:
                raise HTTPException(400, "You have already used this coupon the maximum number of times")

        return coupon

    # --------------------------------------------------
    # 2. Compute discount amount from priced cart items
    # --------------------------------------------------
    @staticmethod
    def compute_discount(
        coupon: Coupon,
        priced_items: List[dict],
    ) -> dict:
        """
        Returns:
            {
                "discount_amount": float,
                "matched_dimension": str | None,
            }
        Raises HTTPException 400 if cart does not qualify.
        """
        if coupon.rule_type == CouponRuleType.PERCENT_CART:
            return CouponService._compute_percent_discount(coupon, priced_items)

        if coupon.rule_type == CouponRuleType.BUY_N_GET_M_SAME_DIMENSION:
            return CouponService._compute_bxgy_discount(coupon, priced_items)

        raise HTTPException(400, "Unknown coupon rule type")

    @staticmethod
    def _compute_percent_discount(coupon: Coupon, priced_items: List[dict]) -> dict:
        subtotal = sum(item["price"] * item["quantity"] for item in priced_items)
        discount = round(subtotal * coupon.percent_off / 100, 2)
        return {"discount_amount": discount, "matched_dimension": None}

    @staticmethod
    def _compute_bxgy_discount(coupon: Coupon, priced_items: List[dict]) -> dict:
        required_qty: int = coupon.required_qty
        free_qty: int = coupon.free_qty

        # Strict: total cart units must exactly equal required_qty
        total_qty = sum(item["quantity"] for item in priced_items)
        if total_qty != required_qty:
            raise HTTPException(
                400,
                f"Coupon requires exactly {required_qty} unit(s) in cart, got {total_qty}",
            )

        # Strict: all units must share one dimension
        dimensions = {item["dimension"] for item in priced_items}
        if len(dimensions) != 1:
            raise HTTPException(
                400,
                "Coupon requires all cart items to have the same dimension",
            )

        matched_dimension = next(iter(dimensions))
        if matched_dimension not in BXGY_ALLOWED_DIMENSIONS:
            raise HTTPException(
                400,
                "Coupon is only applicable to A2, A3, or A4 dimensions",
            )

        # Flatten unit prices by quantity, sort ascending, take first free_qty as free
        unit_prices: List[float] = []
        for item in priced_items:
            unit_prices.extend([item["price"]] * item["quantity"])

        unit_prices.sort()
        discount = round(sum(unit_prices[:free_qty]), 2)

        return {"discount_amount": discount, "matched_dimension": matched_dimension}

    # --------------------------------------------------
    # 3. Record usage after successful order commit
    # --------------------------------------------------
    @staticmethod
    def record_usage(db: Session, coupon_id: int, user_id: str, order_id: int) -> None:
        db.add(CouponUsage(
            coupon_id=coupon_id,
            user_id=user_id,
            order_id=order_id,
        ))

    # --------------------------------------------------
    # 4. List all coupons eligible for a given user
    # --------------------------------------------------
    @staticmethod
    def list_eligible(db: Session, user_id: str) -> List[Coupon]:
        now = datetime.now(timezone.utc)

        coupons = (
            db.query(Coupon)
            .filter(
                Coupon.is_active == True,
                or_(Coupon.starts_at == None, Coupon.starts_at <= now),
                or_(Coupon.ends_at == None, Coupon.ends_at >= now),
            )
            .all()
        )

        eligible = []
        for coupon in coupons:
            # Global usage cap
            if coupon.max_total_uses is not None:
                total_used = db.query(CouponUsage).filter(
                    CouponUsage.coupon_id == coupon.id
                ).count()
                if total_used >= coupon.max_total_uses:
                    continue

            # Per-user usage cap
            if coupon.max_uses_per_user is not None:
                user_used = db.query(CouponUsage).filter(
                    CouponUsage.coupon_id == coupon.id,
                    CouponUsage.user_id == user_id,
                ).count()
                if user_used >= coupon.max_uses_per_user:
                    continue

            eligible.append(coupon)

        return eligible



    
