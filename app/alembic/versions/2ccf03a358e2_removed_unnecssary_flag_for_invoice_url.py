"""removed unnecessary flag for invoice url

Revision ID: 2ccf03a358e2
Revises: 51267894b05d
Create Date: 2026-03-01 19:29:57.347062
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ccf03a358e2'
down_revision: Union[str, Sequence[str], None] = '51267894b05d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("orders", "invoice_generated")


def downgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "invoice_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )