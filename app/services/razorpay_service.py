# app/services/razorpay_service.py
import razorpay
from threading import Lock
import hmac
import hashlib
from core.config import settings

class RazorpayService:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount: float, currency: str = "INR"):
        order_data = {
            "amount": int(amount * 100),  # convert to paise
            "currency": currency,
            "payment_capture": 1,
        }
        return self.client.order.create(order_data)

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify Razorpay payment signature manually.
        """
        generated_sig = hmac.new(
            self.key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(generated_sig, signature)
