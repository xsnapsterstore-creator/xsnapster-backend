from pydantic import BaseModel, Field
from typing import List

class AddressBase(BaseModel):
    name: str = Field(..., example="John Doe")
    address_line: str = Field(..., example="123 Main Street")
    city: str = Field(..., example="New York")
    state: str = Field(..., example="NY")
    zip_code: str = Field(..., example="10001")
    is_default: bool = False
    address_type: str | None = Field(None, example="Home")
    phone_number: str | None = Field(None, example="+1 555 123 4567")

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int
    user_id: str

    class Config:
        from_attributes = True