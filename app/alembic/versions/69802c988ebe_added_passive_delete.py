"""Added passive delete

Revision ID: 69802c988ebe
Revises: 647c2a2e5d27
Create Date: 2025-11-14 07:17:59.747061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69802c988ebe'
down_revision: Union[str, Sequence[str], None] = '647c2a2e5d27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop old FK
    op.drop_constraint(
        "product_analytics_product_id_fkey",
        "product_analytics",
        type_="foreignkey"
    )

    # Create new FK with CASCADE
    op.create_foreign_key(
        "product_analytics_product_id_fkey",
        "product_analytics",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # Drop new FK
    op.drop_constraint(
        "product_analytics_product_id_fkey",
        "product_analytics",
        type_="foreignkey"
    )

    # Recreate old FK without cascade
    op.create_foreign_key(
        "product_analytics_product_id_fkey",
        "product_analytics",
        "products",
        ["product_id"],
        ["id"]
    )
