"""fix coupon enum rename and add check constraints

Revision ID: c1f2a3b4d5e6
Revises: 14aa8a9faa2e
Create Date: 2026-04-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c1f2a3b4d5e6'
down_revision: Union[str, Sequence[str], None] = '14aa8a9faa2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE coupon_rule_type RENAME VALUE 'B2G1_SAME_DIMENSION' TO 'BUY_N_GET_M_SAME_DIMENSION'"
    )
    op.create_check_constraint(
        'ck_coupon_percent_off_range',
        'coupons',
        'percent_off IS NULL OR (percent_off > 0 AND percent_off <= 100)',
    )
    op.create_check_constraint(
        'ck_coupon_required_qty_positive',
        'coupons',
        'required_qty IS NULL OR required_qty > 0',
    )
    op.create_check_constraint(
        'ck_coupon_free_qty_positive',
        'coupons',
        'free_qty IS NULL OR free_qty > 0',
    )
    op.create_check_constraint(
        'ck_coupon_required_gt_free',
        'coupons',
        'required_qty IS NULL OR free_qty IS NULL OR required_qty > free_qty',
    )


def downgrade() -> None:
    op.drop_constraint('ck_coupon_required_gt_free', 'coupons', type_='check')
    op.drop_constraint('ck_coupon_free_qty_positive', 'coupons', type_='check')
    op.drop_constraint('ck_coupon_required_qty_positive', 'coupons', type_='check')
    op.drop_constraint('ck_coupon_percent_off_range', 'coupons', type_='check')
    op.execute(
        "ALTER TYPE coupon_rule_type RENAME VALUE 'BUY_N_GET_M_SAME_DIMENSION' TO 'B2G1_SAME_DIMENSION'"
    )
