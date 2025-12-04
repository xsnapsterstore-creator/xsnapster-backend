from pydantic import BaseModel
from typing import List

class CartItem(BaseModel):
    product_id: int
    dimension: str
    qty: int

class CartRequest(BaseModel):
    items: List[CartItem]
