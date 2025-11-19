from slugify import slugify
from sqlalchemy.orm import Session
from models.products import Category, SubCategory
from typing import Optional, List
from fastapi import HTTPException


def create_or_get_category(
    db: Session,
    category_id: Optional[int] = None,
    name: Optional[str] = None,
    one_liner: Optional[str] = None,
    image_links: Optional[List[str]] = None
) -> Category:
    """
    Get a category by ID or name, or create it if it doesn’t exist.
    """

    # ✅ Case 1: If category_id is provided, fetch directly
    if category_id:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    # ✅ Case 2: Otherwise, create or get by slugified name
    if not name:
        raise HTTPException(status_code=400, detail="Category name is required if no ID is given")

    slug = slugify(name)
    category = db.query(Category).filter(Category.slug == slug).first()

    if not category:
        category = Category(name=name.strip(), slug=slug, one_liner=one_liner, image_links=image_links or [])
        db.add(category)
        db.commit()
        db.refresh(category)

    return category






def get_all_categories(db: Session):
    return db.query(Category).all()


def get_category_by_id(db: Session, category_id: int):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def update_category(db: Session, category_id: int, name: str = None, one_liner: str = None):
    category = get_category_by_id(db, category_id)
    if name:
        category.name = name
    if one_liner:
        category.one_liner = one_liner
    db.commit()
    db.refresh(category)
    return category




def delete_category(db: Session, category_id: int):
    category = get_category_by_id(db, category_id)
    try:
        db.delete(category)
        db.commit()
        return {"message": "Category deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category because products or subcategories are associated with it."
        )


def create_multiple_subcategories(
    db: Session,
    category_id: int,
    subcategory_names: List[str]
) -> List[dict]:
    """
    Creates or retrieves multiple subcategories under the same category.
    Returns a list of subcategory dicts.
    """
    subcategories = []

    for name in subcategory_names:
        name = name.strip()
        slug = slugify(name)

        subcategory = (
            db.query(SubCategory)
            .filter(SubCategory.slug == slug, SubCategory.category_id == category_id)
            .first()
        )

        if not subcategory:
            subcategory = SubCategory(name=name, slug=slug, category_id=category_id)
            db.add(subcategory)
            db.commit()
            db.refresh(subcategory)

        subcategories.append({
            "id": subcategory.id,
            "name": subcategory.name,
            "slug": subcategory.slug,
            "category_id": subcategory.category_id,
        })

    return subcategories

def get_all_subcategories(db: Session):
    return db.query(SubCategory).all()


def get_subcategories_by_category(db: Session, category_id: int):
    return db.query(SubCategory).filter(SubCategory.category_id == category_id).all()


def get_subcategory_by_id(db: Session, subcategory_id: int):
    subcategory = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return subcategory


def update_subcategory(db: Session, subcategory_id: int, name: str = None):
    subcategory = get_subcategory_by_id(db, subcategory_id)
    if name:
        subcategory.name = name
    db.commit()
    db.refresh(subcategory)
    return subcategory


def delete_subcategory(db: Session, subcategory_id: int):
    subcategory = get_subcategory_by_id(db, subcategory_id)
    try:
        db.delete(subcategory)
        db.commit()
        return {"message": "Subcategory deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete subcategory because products are associated with it."
        )
