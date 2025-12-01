from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderSchema(BaseModel):
    id: int
    product_id: int
    razorpay_order_id: Optional[str]
    amount: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
