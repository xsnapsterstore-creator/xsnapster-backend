from typing import List
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.address import AddressResponse
from schemas.orders import OrderSchema

class UserProfileSchema(BaseModel):
    id: str
    email: Optional[str]
    phone_number: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    default_address: Optional[AddressResponse]
    orders: List[OrderSchema] = []

    class Config:
        orm_mode = True
