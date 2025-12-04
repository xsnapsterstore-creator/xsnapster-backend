from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base  # assuming your SQLAlchemy Base is here
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    razorpay_order_id = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)   # total amount
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
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

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    razorpay_payment_id = Column(String, unique=True, index=True)
    razorpay_signature = Column(String)
    amount = Column(Float)
    status = Column(String, default="initiated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship back to order
    order = relationship("Order", back_populates="payment")
