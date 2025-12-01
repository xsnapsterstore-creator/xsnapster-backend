from slugify import slugify
from sqlalchemy.orm import Session
from models.products import Product, ProductAnalytics, Category, SubCategory
from schemas.products import ProductCreate
from datetime import datetime
from sqlalchemy import desc
from typing import Optional, List
from utils.pricing import calculate_dimension_pricing_db





def create_product(db: Session, product_data, image_links: list):
    """
    Create a product linked to existing category and subcategory by ID.
    Does NOT handle dimensions; only base product.
    """
    # --- Validate category ---
    category = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category ID {product_data.category_id} not found")

    # --- Validate subcategory ---
    subcategory = db.query(SubCategory).filter(SubCategory.id == product_data.subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail=f"Subcategory ID {product_data.subcategory_id} not found")

    # --- Ensure subcategory belongs to given category ---
    if subcategory.category_id != category.id:
        raise HTTPException(
            status_code=400,
            detail=f"Subcategory ID {subcategory.id} does not belong to Category ID {category.id}"
        )

    # --- Generate unique slug ---
    base_slug = slugify(product_data.title)
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # --- Create product ---
    db_product = Product(
        title=product_data.title.strip(),
        slug=slug,
        one_liner=product_data.one_liner,
        description=product_data.description,
        image_links=image_links or [],
        is_active=True,
        category_id=category.id,
        subcategory_id=subcategory.id,
        price=product_data.price,
        discounted_price=product_data.discounted_price,
        dimensions=product_data.dimensions, 
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product





def get_product_by_id(db: Session, product_id: int):
    """
    Fetch a product by ID, include its variations (dimensions), category and subcategory names,
    increase view count, and return structured data.
    """
    # Fetch product
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Update analytics (view count)
    analytics = db.query(ProductAnalytics).filter(ProductAnalytics.product_id == product_id).first()
    if not analytics:
        analytics = ProductAnalytics(product_id=product_id, view_count=1)
        db.add(analytics)
    else:
        analytics.view_count += 1
        analytics.updated_at = datetime.utcnow()
    db.commit()


    dimension_pricing = calculate_dimension_pricing_db(
        db,
        product.dimensions or [],
        product.price,
        product.discounted_price
    )



    # Top-level price defaults to first variation


    response = {
        "id": product.id,
        "title": product.title,
        "one_liner": product.one_liner,
        "description": product.description,
        "image_links": product.image_links or [],
        "price": product.price,
        "discounted_price": product.discounted_price,
        "category": product.category_rel.name if product.category_rel else None,
        "subcategory": product.subcategory_rel.name if product.subcategory_rel else None,
        "dimensions": product.dimensions,
        "dimension_pricing": dimension_pricing,
        "slug": product.slug,
        "is_active": product.is_active,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }

    return response

def get_top_products_by_category(db: Session, limit_per_category: int = 4):
    """
    Fetch top N most viewed products for each category,
    including dimension pricing (same as get_product_by_id).
    """
    result = []

    categories = db.query(Category).all()

    for category in categories:
        # Join products with analytics
        products = (
            db.query(Product)
            .outerjoin(ProductAnalytics, ProductAnalytics.product_id == Product.id)
            .filter(Product.category_id == category.id, Product.is_active == True)
            .order_by(ProductAnalytics.view_count.desc().nullslast(), Product.created_at.desc())
            .limit(limit_per_category)
            .all()
        )

        category_products = []
        for p in products:
            # 🔥 Add dimension pricing EXACTLY like get_product_by_id
            dimension_pricing = calculate_dimension_pricing_db(
                db,
                p.dimensions or [],
                p.price,
                p.discounted_price
            )

            category_products.append({
                "id": p.id,
                "title": p.title,
                "one_liner": p.one_liner,
                "slug": p.slug,
                "image_link": (p.image_links[0] if p.image_links else ""),
                "view_count": p.analytics.view_count if p.analytics else 0,
                "price": p.price,
                "discounted_price": p.discounted_price,
                "category": category.name,
                "dimensions": p.dimensions,
                "dimension_pricing": dimension_pricing,     
                "subcategory": p.subcategory_rel.name if p.subcategory_rel else ""
            })

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "products": category_products
        })

    return result


def get_products_by_category(db: Session, category_id: int):
    """
    Fetch all active products of a given category including variations and subcategory names.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")

    products = (
        db.query(Product)
        .filter(Product.category_id == category_id, Product.is_active == True)
        .order_by(Product.created_at.desc())
        .all()
    )

    result = []
    for p in products:
        

        subcategory_name = p.subcategory_rel.name if p.subcategory_rel else None

        result.append({
            "id": p.id,
            "title": p.title,
            "one_liner": p.one_liner,
            "description": p.description,
            "slug": p.slug,
            "image_link": p.image_links[0] or "",
            "category": category.name,
            "subcategory": subcategory_name,
            "dimensions": p.dimensions,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "price": p.price,
            "discounted_price": p.discounted_price
        })

    return result
def get_products_by_subcategory(db: Session, subcategory_id: int):
    """
    Fetch all active products of a given subcategory including variations,
    category names, and dimension pricing.
    """
    subcategory = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail=f"Subcategory with id {subcategory_id} not found")

    products = (
        db.query(Product)
        .filter(Product.subcategory_id == subcategory_id, Product.is_active == True)
        .order_by(Product.created_at.desc())
        .all()
    )

    result = []
    for p in products:

        # 🔥 Get pricing for each dimension
        dimension_pricing = calculate_dimension_pricing_db(
            db,
            p.dimensions or [],
            p.price,
            p.discounted_price
        )

        category_name = p.category_rel.name if p.category_rel else None

        result.append({
            "id": p.id,
            "title": p.title,
            "one_liner": p.one_liner,
            "description": p.description,
            "slug": p.slug,
            "image_link": p.image_links[0] if p.image_links else "",
            "category": category_name,
            "subcategory": subcategory.name,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "dimensions": p.dimensions,
            "dimension_pricing": dimension_pricing,
            "price": p.price,
            "discounted_price": p.discounted_price
        })

    return result

def update_product(db: Session, product_id: int, update_data: dict):
    """
    Update product fields.
    update_data can contain: title, one_liner, description, category_id, subcategory_id, is_active
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    for field, value in update_data.items():
        if hasattr(product, field) and value is not None:
            setattr(product, field, value)

    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int):
    """
    Delete a product and its associated dimensions.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    db.delete(product)
    db.commit()
    return {"message": f"Product {product.title} deleted successfully"}