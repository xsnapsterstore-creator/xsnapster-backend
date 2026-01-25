import razorpay
import hmac
import hashlib
from threading import Lock
from core.config import settings


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

    def create_order(self, amount: float, receipt: str, currency: str = "INR"):
        """Only talks to Razorpay, no DB logic."""
        order_data = {
            "amount": int(amount * 100),
            "currency": currency,
            "payment_capture": 1,
            "receipt": receipt
        }
        return self.client.order.create(order_data)

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Only verifies Razorpay signature."""
        payload = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            self.key_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature
        """
        expected = hmac.new(
               settings.RAZORPAY_WEBHOOK_SECRET.encode(),
               payload,
               hashlib.sha256
            ).hexdigest()

        return hmac.compare_digest(expected, signature)



razorpay_service = RazorpayService()
