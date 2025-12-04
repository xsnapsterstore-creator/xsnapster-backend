import razorpay
from threading import Lock
import hmac
import hashlib
from core.config import settings
from sqlalchemy.orm import Session
from models.order import Order
from models.order import Payment
from datetime import datetime


class RazorpayService:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount: float, currency: str = "INR"):
        print("Creating razorpay order...")
        order_data = {
            "amount": int(amount * 100),
            "currency": currency,
            "payment_capture": 1,
        }
        print("Order data:", order_data)
        return self.client.order.create(order_data)

    def _generate_signature(self, order_id: str, payment_id: str):
        """Internal signature generator."""
        return hmac.new(
            self.key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        generated_sig = self._generate_signature(order_id, payment_id)
        return hmac.compare_digest(generated_sig, signature)

    # ---------------------------------------------------------
    # 🔥 NEW FUNCTION: FULL PAYMENT VERIFY WORKFLOW
    # ---------------------------------------------------------
    def verify_payment(
        self,
        db: Session,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ):
        """
        Full DB + Razorpay signature validation.
        """

        # 1️⃣ Get matching order
        order = (
            db.query(Order)
            .filter(Order.razorpay_order_id == razorpay_order_id)
            .first()
        )

        if not order:
            return {"success": False, "message": "Order not found"}

        # Prevent double verification
        if order.status == "PAID":
            return {"success": True, "message": "Already verified"}

        # 2️⃣ Validate Razorpay signature
        if not self.verify_signature(
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
            signature=razorpay_signature,
        ):
            return {"success": False, "message": "Invalid signature"}

        # 3️⃣ Create/Update payment entry
        payment = Payment(
            order_id=order.id,
            razorpay_payment_id=razorpay_payment_id,
            status="SUCCESS",
            paid_at=datetime.utcnow(),
        )
        db.add(payment)

        # 4️⃣ Update order status
        order.status = "PAID"
        db.commit()
        db.refresh(order)

        return {
            "success": True,
            "message": "Payment verified successfully",
            "order_id": order.id,
        }
