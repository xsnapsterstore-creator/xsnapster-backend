from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.users import Address, User
from schemas.address import AddressCreate, AddressUpdate


def create_address(db: Session, user: User, address_data: AddressCreate):
    """Add new address for a user"""
    # Handle default address logic
    if address_data.is_default:
        db.query(Address).filter(Address.user_id == user.id, Address.is_default == True).update({"is_default": False})

    new_address = Address(user_id=user.id, **address_data.dict())
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


def get_user_addresses(db: Session, user: User):
    """Get all addresses for a given user"""
    addresses = db.query(Address).filter(Address.user_id == user.id).all()
    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found")
    return addresses


def update_user_address(db: Session, user: User, address_id: int, data: AddressUpdate):
    """Update an address for a user"""
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(address, key, value)

    # If making this address default, unset others
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id, Address.id != address.id).update({"is_default": False})

    db.commit()
    db.refresh(address)
    return address


def delete_user_address(db: Session, user: User, address_id: int):
    """Delete a user's address"""
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}
