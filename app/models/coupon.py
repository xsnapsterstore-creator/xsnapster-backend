import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship

from db.base import Base


class CouponRuleType(str, enum.Enum):
    PERCENT_CART = "PERCENT_CART"
    BUY_N_GET_M_SAME_DIMENSION = "BUY_N_GET_M_SAME_DIMENSION"


class Coupon(Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint(
            "percent_off IS NULL OR (percent_off > 0 AND percent_off <= 100)",
            name="ck_coupon_percent_off_range",
        ),
        CheckConstraint(
            "required_qty IS NULL OR required_qty > 0",
            name="ck_coupon_required_qty_positive",
        ),
        CheckConstraint(
            "free_qty IS NULL OR free_qty > 0",
            name="ck_coupon_free_qty_positive",
        ),
        CheckConstraint(
            "required_qty IS NULL OR free_qty IS NULL OR required_qty > free_qty",
            name="ck_coupon_required_gt_free",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)

    rule_type = Column(
        SAEnum(CouponRuleType, name="coupon_rule_type"),
        nullable=False,
    )
    percent_off = Column(Float, nullable=True)
    required_qty = Column(Integer, nullable=True)
    free_qty = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    max_total_uses = Column(Integer, nullable=True)
    max_uses_per_user = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    orders = relationship("Order", back_populates="coupon")
    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    __table_args__ = (
        UniqueConstraint("coupon_id", "user_id", "order_id", name="uq_coupon_user_order"),
        UniqueConstraint("order_id", name="uq_coupon_usage_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", back_populates="coupon_usages")
    order = relationship("Order", back_populates="coupon_usage")
