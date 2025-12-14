from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base  
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

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"))

    delivery_name = Column(String, nullable=False)
    delivery_phone_number = Column(String, nullable=False)
    delivery_address_line = Column(String, nullable=False)
    delivery_city = Column(String, nullable=False)
    delivery_state = Column(String, nullable=False)
    delivery_zip_code = Column(String, nullable=False)
    delivery_address_type = Column(String, nullable=True)

    quantity = Column(Integer, nullable=False, default=1)

    amount = Column(Float, nullable=False)

    # Order lifecycle only (not payment)
    order_status = Column(
        SAEnum(OrderStatus, name="order_status"),
        default=OrderStatus.CREATED,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", uselist=False, back_populates="order")



class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    
    # Price snapshot so price changes don’t break old orders
    price = Column(Float, nullable=False)

    dimension = Column(String, nullable=False)  # e.g. size or other variant info

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")



class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)

    payment_method = Column(String, nullable=False)  # COD | RAZORPAY
    gateway_order_id = Column(String, nullable=True) # Razorpay order_id
    transaction_id = Column(String, nullable=True)   # Razorpay payment_id
    signature = Column(String, nullable=True)

    amount = Column(Float, nullable=False)

   
    status = Column(
        SAEnum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.CREATED,
        nullable=False
    )

    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payment")

