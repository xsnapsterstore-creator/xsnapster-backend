import enum

class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"        # Order created, payment pending
    CONFIRMED = "CONFIRMED"    # Payment successful / COD confirmed
    CANCELLED = "CANCELLED"    # Cancelled by user/system
    SHIPPED = "SHIPPED"        # Shipped by seller
    FULFILLED = "FULFILLED"    # Delivered / completed


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"   # Payment initiated, pending
    SUCCESS = "SUCCESS"   # Payment successful
    FAILED = "FAILED"     # Payment failed