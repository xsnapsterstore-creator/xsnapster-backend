from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from models.products import DimensionPricing

def calculate_dimension_pricing_db(
    db: Session,
    dimensions: List[str],
    base_price: float,
    discounted_price: Optional[float] = None
) -> Dict[str, dict]:
    """
    Dynamically calculate dimension prices using multipliers from the database.
    Falls back to 1.0 multiplier if dimension not found.
    """
    # Fetch all dimension multipliers from DB
    db_dimensions = db.query(DimensionPricing).filter(
        DimensionPricing.name.in_(dimensions)
    ).all()

    # Map names to multipliers
    multiplier_map = {d.name: d.multiplier for d in db_dimensions}

    result = {}
    for dim in dimensions:
        multiplier = multiplier_map.get(dim, 1.0)
        price_for_dim = round(base_price * multiplier, 2)
        discounted_for_dim = (
            round(discounted_price * multiplier, 2)
            if discounted_price is not None
            else None
        )
        result[dim] = {
            "price": price_for_dim,
            "discounted_price": discounted_for_dim,
            "multiplier": multiplier
        }

    return result
