from fastapi import APIRouter, HTTPException, Form, Depends, File, UploadFile
from sqlalchemy.orm import Session
from slugify import slugify
from models.products import Category
from db.session import get_db
from services.category_service import *
from typing import Optional, List
from services.s3_service import s3_service




category_router = APIRouter(prefix="/v1/category", tags=["Category"])


@category_router.post("/")
async def add_category(
    name: str = Form(...),
    one_liner: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    image_links = []
    for image in images:
        try:
            await image.seek(0)
            url = await s3_service.upload_image(image)
            image_links.append(url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {image.filename}: {str(e)}")

    category = create_or_get_category(db, name=name, one_liner=one_liner, image_links=image_links)
    return category




@category_router.get("/")
def list_categories(db: Session = Depends(get_db)):
    return get_all_categories(db)

@category_router.get("/{category_id}")
def retrieve_category(category_id: int, db: Session = Depends(get_db)):
    return get_category_by_id(db, category_id)

@category_router.put("/{category_id}")
def edit_category(
    category_id: int,
    name: str = Form(None),
    one_liner: str = Form(None),
    db: Session = Depends(get_db)
):
    return update_category(db, category_id, name, one_liner)

@category_router.delete("/{category_id}")
def remove_category(category_id: int, db: Session = Depends(get_db)):
    return delete_category(db, category_id)

########################################################################################   

subcategory_router = APIRouter(prefix="/v1/subcategory", tags=["SubCategory"])

@subcategory_router.post("/")
async def add_subcategories(
    category_id: Optional[int] = Form(None),
    category_name: Optional[str] = Form(None),
    category_one_liner: Optional[str] = Form(None),
    subcategory_names: List[str] = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    """
    Creates multiple subcategories under an existing category.
    If category_id is not provided, category_name will be used to create/get category.
    """
    print('subcategory_names', subcategory_names)
    if not category_id and not category_name:
        raise HTTPException(status_code=400, detail="Either category_id or category_name is required")

     
    image_links = []
    for image in images:
        try:
            await image.seek(0)
            url = await s3_service.upload_image(image)
            image_links.append(url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {image.filename}: {str(e)}")

    print(image_links)


    category = create_or_get_category(
        db=db,
        category_id=category_id,
        name=category_name,
        one_liner=category_one_liner,
        image_links=image_links
    )

    subcategories = create_multiple_subcategories(
        db=db,
        category_id=category.id,
        subcategory_names=subcategory_names
    )

    return {
        "category": {"id": category.id, "name": category.name},
        "subcategories": subcategories
    }

@subcategory_router.get("/")
def list_subcategories(db: Session = Depends(get_db)):
    print('here')
    return get_all_subcategories(db)

@subcategory_router.get("/{category_id}")
def list_subcategories_for_category(category_id: int, db: Session = Depends(get_db)):
    return get_subcategories_by_category(db, category_id)

@subcategory_router.put("/{subcategory_id}")
def edit_subcategory(
    subcategory_id: int,
    name: str = Form(None),
    db: Session = Depends(get_db)
):
    return update_subcategory(db, subcategory_id, name)

@subcategory_router.delete("/{subcategory_id}")
def remove_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    return delete_subcategory(db, subcategory_id)


