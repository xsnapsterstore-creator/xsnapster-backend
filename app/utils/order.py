# # app/utils/payments.py
# from fastapi import HTTPException
# from sqlalchemy.orm import Session
# from models.order import Order, Payment, OrderStatus
# from models.products import Product
# from services.razorpay_service import RazorpayService

# razorpay = RazorpayService()

# def create_order_util(product_id: int, db: Session):
#     """Create a Razorpay order and store it in DB"""

#     product = db.query(Product).filter(Product.id == product_id).first()
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     # create order in Razorpay
#     order_data = razorpay.create_order(amount=product.price)

#     order = Order(
#         product_id=product.id,
#         razorpay_order_id=order_data["id"],
#         amount=product.price,
#         status=OrderStatus.PENDING,
#     )
#     db.add(order)
#     db.commit()
#     db.refresh(order)

#     return {
#         "order_id": order_data["id"],
#         "razorpay_key": razorpay.key_id,
#         "amount": product.price,
#         "currency": "INR",
#     }



# def verify_payment_util(order_id: str, payment_id: str, signature: str, db: Session):
#     """Verify payment signature and record payment"""

#     if not razorpay.verify_signature(order_id, payment_id, signature):
#         raise HTTPException(status_code=400, detail="Invalid payment signature")

#     order = db.query(Order).filter(Order.razorpay_order_id == order_id).first()
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")

#     existing_payment = db.query(Payment).filter(
#         Payment.razorpay_payment_id == payment_id
#     ).first()
#     if existing_payment:
#         raise HTTPException(status_code=400, detail="Payment already processed")

#     payment = Payment(
#         order_id=order.id,
#         razorpay_payment_id=payment_id,
#         razorpay_signature=signature,
#         amount=order.amount,
#         status="paid",
#     )

#     order.status = OrderStatus.PAID
#     db.add(payment)
#     db.commit()
#     db.refresh(payment)

#     return {
#         "status": "success",
#         "message": "Payment verified successfully!",
#         "order_id": order.id,
#         "payment_id": payment.id,
#     }


from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.order import Order, OrderItem
from models.products import Product
from services.razorpay_service import RazorpayService
from utils.pricing import calculate_dimension_pricing_db

razorpay_service = RazorpayService()

class OrderService:

    @staticmethod
    def create_order(db: Session, user_id: str, items: List[dict]):
        """
        items: list of dicts with keys: product_id, quantity, dimension
        """

        if not items:
            raise HTTPException(status_code=400, detail="Cart cannot be empty")

        # Collect product ids and validate shape
        product_ids = [i["product_id"] for i in items]
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}

        order_total = 0.0
        order_items_data = []
        print(items)
        # Validate every cart item and compute unit prices using dimension multipliers
        for item in items:
            pid = item.get("product_id")
            qty = item.get("qty")
            dim = item.get("dimension")

            if pid not in product_map:
                raise HTTPException(status_code=400, detail=f"Invalid product: {pid}")

            if not isinstance(qty, int) or qty <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be integer >= 1")

            product = product_map[pid]

            # Validate the requested dimension exists on the product
            if not product.dimensions or dim not in product.dimensions:
                raise HTTPException(status_code=400, detail=f"Invalid dimension '{dim}' for product {pid}")

            # Use helper to get price for this dimension (you can batch, but for clarity we call it per product)
            pricing_map = calculate_dimension_pricing_db(
                db=db,
                dimensions=[dim],
                base_price=product.price,
                discounted_price=product.discounted_price
            )
            print(pricing_map)

            dim_pricing = pricing_map.get(dim)
            if not dim_pricing:
                raise HTTPException(status_code=500, detail="Dimension pricing error")

            # Use discounted price if available, otherwise normal price
            unit_price = dim_pricing["discounted_price"] if dim_pricing["discounted_price"] is not None else dim_pricing["price"]
            unit_price = float(round(unit_price, 2))

            line_total = unit_price * qty
            order_total += line_total

            print("here")

            order_items_data.append({
                "product_id": pid,
                "quantity": qty,
                "price": unit_price,   # snapshot unit price
                "dimension": dim
            })
        print("there")
        # Create Razorpay order using calculated total
        razorpay_order = razorpay_service.create_order(order_total)
        razorpay_order_id = razorpay_order["id"]

        # Persist Order
        order = Order(
            user_id=user_id,
            amount=order_total,
            razorpay_order_id=razorpay_order_id,
            status="PENDING"
        )
        db.add(order)
        db.flush()  # populate order.id

        # Persist OrderItems
        for it in order_items_data:
            print(it)
            db.add(OrderItem(order_id=order.id, **it))

        db.commit()
        db.refresh(order)

        # Return minimal payload to frontend
        return {
            "order_id": order.id,
            "razorpay_order_id": razorpay_order_id,
            "amount": order_total,
            "currency": "INR",
            "items": order_items_data
        }
