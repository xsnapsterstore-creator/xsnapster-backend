"""add order pricing breakdown columns

Revision ID: 9d31b6c4a7f2
Revises: 2ccf03a358e2
Create Date: 2026-04-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d31b6c4a7f2"
down_revision: Union[str, Sequence[str], None] = "2ccf03a358e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "items_subtotal",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "delivery_charge",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
    )

    op.execute(
        """
        UPDATE orders o
        SET items_subtotal = COALESCE(oi.sum_items, 0)
        FROM (
            SELECT order_id, SUM(price * quantity) AS sum_items
            FROM order_items
            GROUP BY order_id
        ) oi
        WHERE o.id = oi.order_id
        """
    )

    op.execute(
        """
        UPDATE orders
        SET delivery_charge = GREATEST(amount - COALESCE(items_subtotal, 0), 0)
        """
    )

    op.alter_column("orders", "items_subtotal", nullable=False)
    op.alter_column("orders", "delivery_charge", nullable=False)


def downgrade() -> None:
    op.drop_column("orders", "delivery_charge")
    op.drop_column("orders", "items_subtotal")
