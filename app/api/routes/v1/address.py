from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from core.security import get_current_user
from services.address_service import (
    create_address,
    get_user_addresses,
    update_user_address,
    delete_user_address
)
from typing import List
from models.users import User

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_address(db, current_user, address_data)


@router.get("/", response_model=List[AddressResponse])
def list_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_addresses(db, current_user)


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_user_address(db, current_user, address_id, address_data)


@router.delete("/{address_id}", status_code=status.HTTP_200_OK)
def remove_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_user_address(db, current_user, address_id)
