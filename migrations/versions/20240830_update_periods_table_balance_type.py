"""update periods table's balance type

Revision ID: c670c25e8024
Revises: 75209dd98f73
Create Date: 2024-08-30 19:07:39.097864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c670c25e8024'
down_revision: Union[str, None] = '75209dd98f73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('daily_feature_holding_balance_merchantmoe', 'token0_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_merchantmoe', 'token1_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_staked_fbtc_detail', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_uniswap_v3', 'token0_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_uniswap_v3', 'token1_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'balance_of',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'total_supply',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'token0_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'token1_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_lendle', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_merchantmoe', 'token0_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_merchantmoe', 'token1_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_staked_fbtc_detail', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_uniswap_v3', 'token0_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_uniswap_v3', 'token1_balance',
               existing_type=sa.NUMERIC(precision=78, scale=0),
               type_=sa.NUMERIC(precision=100, scale=18),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('period_feature_holding_balance_uniswap_v3', 'token1_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_uniswap_v3', 'token0_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_staked_fbtc_detail', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=100, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_merchantmoe', 'token1_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_merchantmoe', 'token0_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_lendle', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=100, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'token1_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'token0_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'total_supply',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('period_feature_holding_balance_dodo', 'balance_of',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_uniswap_v3', 'token1_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_uniswap_v3', 'token0_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_staked_fbtc_detail', 'balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=100, scale=0),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_merchantmoe', 'token1_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    op.alter_column('daily_feature_holding_balance_merchantmoe', 'token0_balance',
               existing_type=sa.NUMERIC(precision=100, scale=18),
               type_=sa.NUMERIC(precision=78, scale=0),
               existing_nullable=True)
    # ### end Alembic commands ###
