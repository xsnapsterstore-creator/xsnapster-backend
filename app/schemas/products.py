from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Base schema for shared fields
class ProductBase(BaseModel):
    title: str
    one_liner: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    slug: Optional[str] = None  
    price: float
    discounted_price: Optional[float] = None
    dimensions: Optional[List[str]] = []

class ProductCreate(ProductBase):
    pass



        


class ProductAnalyticsSchema(BaseModel):
    view_count: int
    purchase_count: int
    rating: float
    review_count: int
    stock_count: int
    wishlist_count: int

    class Config:
        from_attributes = True









class ProductResponse(BaseModel):
    id: int
    title: str
    one_liner: Optional[str]
    description: Optional[str]
    image_links: List[str] = []
    price: float
    discounted_price: Optional[float]
    category: Optional[str]
    subcategory: Optional[str]
    slug: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    dimensions: Optional[List[str]] = []
    dimension_pricing: Optional[dict] = None

    class Config:
        from_attributes = True 

class PaginatedProducts(BaseModel):
    page: int
    limit: int
    total: int
    pages: int
    data: List[ProductResponse]  # list of products

    class Config:
        from_attributes = True