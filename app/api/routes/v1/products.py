from fastapi import APIRouter, Depends, Response, Request, HTTPException, status, Body, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from db.session import get_db
from services.auth_service import request_otp, verify_otp_and_issue_tokens, refresh_tokens
from schemas.products import ProductCreate, ProductResponse, PaginatedProducts
from typing import List, Optional
from services.product_service import *
from services.s3_service import s3_service
from models.users import User
from core.security import get_current_user_with_email_check


router = APIRouter(prefix="/v1/products", tags=["Products"])


@router.post("/", response_model=dict)
async def add_product(
    title: str = Form(...),
    one_liner: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    subcategory_id: int = Form(...),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    price: float = Form(...),
    discounted_price: Optional[float] = Form(None),
    dimensions: List[str] = Form([]),
    admin_user: User = Depends(get_current_user_with_email_check)
):
    dimensions = dimensions or ["A4","A3","A2","Poster"]

    image_links = []
    for image in images:
        try:
            await image.seek(0)
            url = await s3_service.upload_image(image)
            image_links.append(url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {image.filename}: {str(e)}")

    # --- Prepare product data ---
    product_data = ProductCreate(
        title=title,
        one_liner=one_liner,
        description=description,
        category_id=category_id,
        subcategory_id=subcategory_id,
        price=price,
        discounted_price=discounted_price,
        dimensions=dimensions
    )

    # --- Create product ---
    product = create_product(db, product_data=product_data, image_links=image_links)

    return {
        "message": "Product created successfully",
        "product_id": product.id,
        "slug": product.slug,
        "category_id": category_id,
        "subcategory_id": subcategory_id,
        "images_uploaded": len(image_links),
        "price": price,
        "discounted_price": discounted_price

    }

# @router.get("/", response_model=PaginatedProducts)
# def list_products(
#     db: Session = Depends(get_db),
#     page: int = Query(1, ge=1),
#     limit: int = Query(10, ge=1, le=100),
#     category: Optional[str] = None,
#     subcategory: Optional[str] = None,
#     search: Optional[str] = None,
#     is_active: Optional[bool] = True,
#     sort_by: Optional[str] = Query(None, description="Field to sort by: price, created_at, title, discounted_price"),
#     sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
# ):
#     products, total = get_products_paginated(
#         db=db,
#         page=page,
#         limit=limit,
#         category=category,
#         subcategory=subcategory,
#         search=search,
#         is_active=is_active,
#         sort_by=sort_by,
#         sort_order=sort_order,
#     )

#     return {
#         "page": page,
#         "limit": limit,
#         "total": total,
#         "pages": (total + limit - 1) // limit,
#         "data": products,
#     }

@router.get("/top-viewed", response_model=list)
def list_top_viewed_products(db: Session = Depends(get_db)):
    """
    List top 4 most viewed products for each category.
    """
    
    return get_top_products_by_category(db=db, limit_per_category=4)

@router.get("/category/{category_id}", response_model=list)
def list_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    List all active products for a specific category.
    """
    return get_products_by_category(db=db, category_id=category_id)


@router.get("/subcategory/{subcategory_id}", response_model=list)
def list_products_by_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    """
    List all active products for a specific subcategory.
    """
    return get_products_by_subcategory(db=db, subcategory_id=subcategory_id)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    API endpoint to get a product by ID including its variations.
    """
    return get_product_by_id(db, product_id)


@router.put("/{product_id}", response_model=dict)
def edit_product(
    product_id: int,
    title: str = Form(None),
    one_liner: str = Form(None),
    description: str = Form(None),
    category_id: int = Form(None),
    subcategory_id: int = Form(None),
    is_active: bool = Form(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user_with_email_check)
):
    """
    Update product fields.
    """
    update_data = {
        "title": title,
        "one_liner": one_liner,
        "description": description,
        "category_id": category_id,
        "subcategory_id": subcategory_id,
        "is_active": is_active
    }

    product = update_product(db, product_id, update_data)
    return {
        "message": "Product updated successfully",
        "product_id": product.id,
        "slug": product.slug
    }


@router.delete("/{product_id}", response_model=dict)
def remove_product(product_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_user_with_email_check)):
    """
    Delete a product and its variations.
    """
    return delete_product(db, product_id)
