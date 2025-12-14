from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.order import Order, OrderItem, Payment, OrderStatus, PaymentStatus
from models.products import Product
from services.razorpay_service import razorpay_service
from utils.pricing import calculate_dimension_pricing_db
from models.users import Address


class OrderService:

    @staticmethod
    def create_order(
        db: Session,
        user_id: str,
        items: List[dict],
        address_id: int,
        payment_method: str
    ):
        if not items:
            raise HTTPException(400, "Cart cannot be empty")

        # 1️⃣ Fetch & validate address
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == user_id
        ).first()

        if not address:
            raise HTTPException(404, "Address not found")

        # 2️⃣ Validate items & pricing
        priced_items, order_total, total_quantity = OrderService._validate_and_price_items(db, items)


        # 3️⃣ Create order with address SNAPSHOT
        order = Order(
            user_id=user_id,
            delivery_name=address.name,
            delivery_phone_number=address.phone_number,
            delivery_address_line=address.address_line,
            delivery_city=address.city,
            delivery_state=address.state,
            delivery_zip_code=address.zip_code,
            delivery_address_type=address.address_type,
            amount=order_total,
            quantity=total_quantity,   # ✅ NEW
            order_status=OrderStatus.CREATED
        )

        db.add(order)
        db.flush()  # generate order.id

        # 4️⃣ Create order items
        for item in priced_items:
            db.add(OrderItem(order_id=order.id, **item))

        # 5️⃣ Create payment
        payment_response = OrderService._create_payment(
            db=db,
            order=order,
            payment_method=payment_method,
            amount=order_total
        )

        db.commit()
        db.refresh(order)

        return {
            "order_id": order.id,
            "amount": order_total,
            "currency": "INR",
            "payment_method": payment_method,
            **payment_response,
            "items": priced_items
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
            razorpay_order = razorpay_service.create_order(amount)

            print("Created Razorpay order:", razorpay_order)

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
