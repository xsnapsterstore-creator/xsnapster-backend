from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.order import Order, OrderItem, Payment
from schemas.payment import OrderStatus, PaymentStatus
from models.products import Product
from services.razorpay_service import razorpay_service
from services.delivery_charge_service import (
    DeliveryChargePolicy,
    build_pricing_breakdown,
)
from services.coupon_service import CouponService
from utils.pricing import calculate_dimension_pricing_db
from models.users import Address
from db.session import get_db_session
from core.config import settings


class OrderService:

    @staticmethod
    def _get_delivery_policy() -> DeliveryChargePolicy:
        return DeliveryChargePolicy(
            base_charge=settings.DELIVERY_BASE_CHARGE,
            free_delivery_threshold=settings.DELIVERY_FREE_THRESHOLD,
        )

    @staticmethod
    def _build_existing_order_pricing_summary(order: Order) -> dict:
        """
        Reconstruct pricing split from persisted order snapshot.
        This keeps idempotent responses stable without relying on mutable state.
        """
        items_subtotal = round(float(order.items_subtotal or 0.0), 2)
        delivery_charge = round(float(order.delivery_charge or 0.0), 2)

        return {
            "items_subtotal": items_subtotal,
            "delivery_charge": max(delivery_charge, 0.0),
            "amount": float(order.amount),
        }

    @staticmethod
    def create_order(
        db: Session,
        user_id: str,
        items: List[dict],
        address_id: int,
        payment_method: str,
        idempotency_key: str,
        coupon_code: Optional[str] = None,
    ):
        if not items:
            raise HTTPException(400, "Cart cannot be empty")

        # ⭐ STEP 1: EARLY idempotency check
        existing_order = (
            db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.idempotency_key == idempotency_key
            )
            .first()
        )

        if existing_order:
            payment = existing_order.payment
            pricing_summary = OrderService._build_existing_order_pricing_summary(
                existing_order
            )

            return {
                "order_id": existing_order.id,
                **pricing_summary,
                "currency": "INR",
                "payment_method": payment.payment_method,
                "payment_status": payment.status,
                "payment_gateway_order_id": payment.gateway_order_id,
                "items": [
                    {
                        "product_id": oi.product_id,
                        "quantity": oi.quantity,
                        "price": oi.price,
                        "dimension": oi.dimension
                    }
                    for oi in existing_order.items
                ]
            }

        # 1️⃣ Fetch & validate address
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == user_id
        ).first()

        if not address:
            raise HTTPException(404, "Address not found")

        # 2️⃣ Validate items & pricing
        priced_items, items_subtotal, total_quantity = (
            OrderService._validate_and_price_items(db, items)
        )

        # 3️⃣ Apply coupon if provided
        coupon = None
        coupon_discount_amount = 0.0
        subtotal_before_coupon = None
        subtotal_after_coupon = None
        matched_dimension = None

        if coupon_code:
            coupon = CouponService.fetch_and_validate(db, coupon_code, user_id)
            discount_result = CouponService.compute_discount(coupon, priced_items)
            coupon_discount_amount = discount_result["discount_amount"]
            matched_dimension = discount_result["matched_dimension"]
            subtotal_before_coupon = items_subtotal
            items_subtotal = round(max(items_subtotal - coupon_discount_amount, 0.0), 2)
            subtotal_after_coupon = items_subtotal

        pricing_summary = build_pricing_breakdown(
            subtotal=items_subtotal,
            policy=OrderService._get_delivery_policy(),
        )

        order_total = pricing_summary["amount"]

        # 4️⃣ Create order
        order = Order(
            user_id=user_id,
            idempotency_key=idempotency_key,
            delivery_name=address.name,
            delivery_phone_number=address.phone_number,
            delivery_address_line=address.address_line,
            delivery_city=address.city,
            delivery_state=address.state,
            delivery_zip_code=address.zip_code,
            delivery_address_type=address.address_type,
            items_subtotal=subtotal_before_coupon or items_subtotal,
            subtotal_before_coupon=subtotal_before_coupon,
            coupon_discount_amount=coupon_discount_amount,
            subtotal_after_coupon=subtotal_after_coupon,
            coupon_id=coupon.id if coupon else None,
            coupon_code=coupon.code if coupon else None,
            coupon_type=coupon.rule_type.value if coupon else None,
            coupon_required_qty=coupon.required_qty if coupon else None,
            coupon_free_qty=coupon.free_qty if coupon else None,
            coupon_matched_dimension=matched_dimension,
            delivery_charge=pricing_summary["delivery_charge"],
            amount=order_total,
            quantity=total_quantity,
            order_status=OrderStatus.CREATED
        )

        db.add(order)
        db.flush()  # generate order.id

        # 5️⃣ Create order items
        for item in priced_items:
            db.add(OrderItem(order_id=order.id, **item))

        # 6️⃣ Record coupon usage (committed atomically with the order)
        if coupon:
            CouponService.record_usage(db, coupon.id, user_id, order.id)

        # 7️⃣ Create payment
        payment_response = OrderService._create_payment(
            db=db,
            order=order,
            payment_method=payment_method,
            amount=order_total
        )

        # ⭐ STEP 6: COMMIT WITH RACE CONDITION PROTECTION
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            # Another request already created this order
            order = (
                db.query(Order)
                .filter(
                    Order.user_id == user_id,
                    Order.idempotency_key == idempotency_key
                )
                .first()
            )

            payment = order.payment

            return {
                "order_id": order.id,
                **OrderService._build_existing_order_pricing_summary(order),
                "currency": "INR",
                "payment_method": payment.payment_method,
                "payment_status": payment.status,
                "payment_gateway_order_id": payment.gateway_order_id,
            }

        db.refresh(order)

        if payment_method == "COD":
            from tasks.process_order import process_confirmed_order
            from tasks.notify_admin import notify_admin

            process_confirmed_order.send(order.id)
            notify_admin.send(order.id)

        applied_coupon = None
        if coupon:
            applied_coupon = {
                "id": coupon.id,
                "code": coupon.code,
                "rule_type": coupon.rule_type.value,
                "percent_off": coupon.percent_off,
                "required_qty": coupon.required_qty,
                "free_qty": coupon.free_qty,
                "matched_dimension": matched_dimension,
            }

        return {
            "order_id": order.id,
            "subtotal_before_coupon": subtotal_before_coupon,
            "coupon_discount_amount": coupon_discount_amount,
            "subtotal_after_coupon": subtotal_after_coupon,
            **pricing_summary,
            "currency": "INR",
            "payment_method": payment_method,
            **payment_response,
            "applied_coupon": applied_coupon,
            "items": priced_items,
        }

    # --------------------------------------------------
    # Validate items + calculate price
    # --------------------------------------------------
    @staticmethod
    def _validate_and_price_items(db: Session, items: List[dict]):
        product_ids = [i["product_id"] for i in items]
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}

        priced_items = []
        order_total = 0.0
        total_quantity = 0

        for item in items:
            pid = item["product_id"]
            qty = item["qty"]
            dim = item["dimension"]

            if pid not in product_map:
                raise HTTPException(400, f"Invalid product: {pid}")

            if qty <= 0:
                raise HTTPException(400, "Quantity must be >= 1")

            product = product_map[pid]

            if not product.dimensions or dim not in product.dimensions:
                raise HTTPException(400, f"Invalid dimension '{dim}' for product {pid}")

            pricing = calculate_dimension_pricing_db(
                db=db,
                dimensions=[dim],
                base_price=product.price,
                discounted_price=product.discounted_price
            )[dim]

            unit_price = float(pricing["discounted_price"] or pricing["price"])
            line_total = unit_price * qty
            order_total += line_total
            total_quantity += qty


            priced_items.append({
                "product_id": pid,
                "quantity": qty,
                "price": unit_price,
                "dimension": dim
            })

        return priced_items, round(order_total, 2), total_quantity

    # --------------------------------------------------
    # Create payment record (COD / Razorpay)
    # --------------------------------------------------
    @staticmethod
    def _create_payment(
        db: Session,
        order: Order,
        payment_method: str,
        amount: float
    ):
        if payment_method == "COD":
            payment = Payment(
                order_id=order.id,
                payment_method="COD",
                amount=amount,
                status=PaymentStatus.SUCCESS
            )

            order.order_status = OrderStatus.CONFIRMED

            db.add(payment)

            return {
                "payment_status": PaymentStatus.SUCCESS
            }

        if payment_method == "RAZORPAY":
            razorpay_order = razorpay_service.create_order(amount, receipt=str(order.id))   


            payment = Payment(
                order_id=order.id,
                payment_method="RAZORPAY",
                gateway_order_id=razorpay_order["id"],
                amount=amount,
                status=PaymentStatus.CREATED
            )

            db.add(payment)

            return {
                "payment_status": "CREATED",
                "payment_gateway_order_id": razorpay_order["id"]
            }

        raise HTTPException(400, f"Unsupported payment method: {payment_method}")






def get_order_by_id(order_id: int, db: Session):

    return db.query(Order).filter(Order.id == order_id).first()