"""Simplified orders, payments table

Revision ID: 4a43fe8eea49
Revises: e7c069da6150
Create Date: 2025-12-13 13:34:59
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ─────────────────────────────────────────────────────
# Alembic identifiers
# ─────────────────────────────────────────────────────
revision: str = "4a43fe8eea49"
down_revision: Union[str, Sequence[str], None] = "e7c069da6150"
branch_labels = None
depends_on = None

# ─────────────────────────────────────────────────────
# ENUM definitions (Postgres native)
# ─────────────────────────────────────────────────────
order_status_enum = postgresql.ENUM(
    'CREATED',
    'CONFIRMED',
    'CANCELLED',
    'SHIPPED',
    'FULFILLED',
    name='order_status'
)

payment_status_enum = postgresql.ENUM(
    'CREATED',
    'SUCCESS',
    'FAILED',
    name='payment_status'
)


def upgrade() -> None:
    bind = op.get_bind()

    # 1️⃣ Create ENUM types FIRST
    order_status_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)

    # 2️⃣ orders.order_status → ENUM
    op.alter_column(
        'orders',
        'order_status',
        existing_type=sa.VARCHAR(),
        type_=order_status_enum,
        postgresql_using="order_status::order_status",
        existing_nullable=True,
    )

    # 3️⃣ Remove payment fields from orders
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'payment_method')
    op.drop_column('orders', 'payment_gateway_order_id')

    # 4️⃣ Payments table updates
    op.add_column(
        'payments',
        sa.Column('gateway_order_id', sa.String(), nullable=True)
    )

    op.alter_column(
        'payments',
        'payment_method',
        existing_type=sa.VARCHAR(),
        nullable=False
    )

    op.alter_column(
        'payments',
        'amount',
        existing_type=sa.DOUBLE_PRECISION(),
        nullable=False
    )

    op.alter_column(
        'payments',
        'status',
        existing_type=sa.VARCHAR(),
        type_=payment_status_enum,
        postgresql_using="status::payment_status",
        existing_nullable=True
    )

    # 5️⃣ One payment per order
    op.create_unique_constraint(
        'uq_payments_order_id',
        'payments',
        ['order_id']
    )


def downgrade() -> None:
    bind = op.get_bind()

    # 1️⃣ Remove constraint
    op.drop_constraint(
        'uq_payments_order_id',
        'payments',
        type_='unique'
    )

    # 2️⃣ Convert ENUMs → VARCHAR
    op.alter_column(
        'payments',
        'status',
        existing_type=payment_status_enum,
        type_=sa.VARCHAR(),
        existing_nullable=True
    )

    op.alter_column(
        'payments',
        'amount',
        existing_type=sa.DOUBLE_PRECISION(),
        nullable=True
    )

    op.alter_column(
        'payments',
        'payment_method',
        existing_type=sa.VARCHAR(),
        nullable=True
    )

    op.drop_column('payments', 'gateway_order_id')

    # 3️⃣ Restore orders payment columns
    op.add_column(
        'orders',
        sa.Column('payment_gateway_order_id', sa.String(), nullable=True)
    )
    op.add_column(
        'orders',
        sa.Column('payment_method', sa.String(), nullable=False)
    )
    op.add_column(
        'orders',
        sa.Column('payment_status', sa.String(), nullable=True)
    )

    op.alter_column(
        'orders',
        'order_status',
        existing_type=order_status_enum,
        type_=sa.VARCHAR(),
        existing_nullable=True
    )

    # 4️⃣ Drop ENUM types LAST
    payment_status_enum.drop(bind, checkfirst=True)
    order_status_enum.drop(bind, checkfirst=True)
