from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from models.products import DimensionPricing


def round_price_to_9(value: float) -> int:
    value = int(round(value))  # remove decimals
    remainder = value % 10
    return value if remainder == 9 else value + (9 - remainder)

from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from models.products import DimensionPricing


def round_price_to_9(value: float) -> int:
    value = int(round(value))
    remainder = value % 10
    return value if remainder == 9 else value + (9 - remainder)


def calculate_dimension_pricing_db(
    db: Session,
    dimensions: List[str],
    base_price: float,
    discounted_price: Optional[float] = None
) -> Dict[str, dict]:
    """
    Dynamically calculate dimension prices using multipliers from the database.
    Prices are rounded to end with 9 and have no decimals.
    """

    db_dimensions = db.query(DimensionPricing).filter(
        DimensionPricing.name.in_(dimensions)
    ).all()

    multiplier_map = {d.name: d.multiplier for d in db_dimensions}

    result = {}
    for dim in dimensions:
        multiplier = multiplier_map.get(dim, 1.0)

        price_for_dim = round_price_to_9(base_price * multiplier)

        discounted_for_dim = (
            round_price_to_9(discounted_price * multiplier)
            if discounted_price is not None
            else None
        )

        result[dim] = {
            "price": price_for_dim,
            "discounted_price": discounted_for_dim,
            "multiplier": multiplier
        }

    return result
