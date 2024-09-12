"""add uniswap merchant daily table

Revision ID: c609922eae7a
Revises: 3dd9b90d2e31
Create Date: 2024-09-12 14:44:05.528650

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c609922eae7a"
down_revision: Union[str, None] = "3dd9b90d2e31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "af_holding_balance_merchantmoe_period",
        sa.Column("period_date", sa.DATE(), nullable=False),
        sa.Column("protocol_id", sa.VARCHAR(), nullable=False),
        sa.Column("contract_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token0_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token0_symbol", sa.VARCHAR(), nullable=False),
        sa.Column("token0_balance", sa.NUMERIC(precision=100, scale=18), nullable=True),
        sa.Column("token1_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token1_symbol", sa.VARCHAR(), nullable=False),
        sa.Column("token1_balance", sa.NUMERIC(precision=100, scale=18), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("period_date", "protocol_id", "contract_address", "token_id", "wallet_address"),
    )
    op.create_index(
        "af_holding_balance_merchantmoe_period_period_date",
        "af_holding_balance_merchantmoe_period",
        ["period_date"],
        unique=False,
    )
    op.create_table(
        "af_holding_balance_uniswap_v3_period",
        sa.Column("period_date", sa.DATE(), nullable=False),
        sa.Column("protocol_id", sa.VARCHAR(), nullable=False),
        sa.Column("contract_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.INTEGER(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token0_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token0_symbol", sa.VARCHAR(), nullable=False),
        sa.Column("token0_balance", sa.NUMERIC(precision=100, scale=18), nullable=True),
        sa.Column("token1_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token1_symbol", sa.VARCHAR(), nullable=False),
        sa.Column("token1_balance", sa.NUMERIC(precision=100, scale=18), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("period_date", "protocol_id", "contract_address", "token_id"),
    )
    op.create_index(
        "af_holding_balance_uniswap_v3_period_period_date",
        "af_holding_balance_uniswap_v3_period",
        ["period_date"],
        unique=False,
    )
    op.create_table(
        "af_merchant_moe_token_bin_hist_period",
        sa.Column("period_date", sa.DATE(), nullable=False),
        sa.Column("position_token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("reserve0_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("reserve1_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("period_date", "position_token_address", "token_id"),
    )
    op.create_table(
        "af_uniswap_v3_pool_prices_daily",
        sa.Column("block_date", sa.DATE(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=78), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("block_date", "pool_address"),
    )
    op.create_index(
        "af_uniswap_v3_pool_prices_daily_block_date_index",
        "af_uniswap_v3_pool_prices_daily",
        ["block_date"],
        unique=False,
    )
    op.create_table(
        "af_uniswap_v3_pool_prices_period",
        sa.Column("period_date", sa.DATE(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=78), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("period_date", "pool_address"),
    )
    op.create_index(
        "af_uniswap_v3_pool_prices_period_period_date_index",
        "af_uniswap_v3_pool_prices_period",
        ["period_date"],
        unique=False,
    )
    op.create_table(
        "af_uniswap_v3_token_data_daily",
        sa.Column("block_date", sa.DATE(), nullable=False),
        sa.Column("position_token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.INTEGER(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("liquidity", sa.NUMERIC(precision=78), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("block_date", "position_token_address", "token_id"),
    )
    op.create_index(
        "af_uniswap_v3_token_data_daily_index", "af_uniswap_v3_token_data_daily", ["block_date"], unique=False
    )
    op.create_table(
        "af_uniswap_v3_token_data_period",
        sa.Column("period_date", sa.DATE(), nullable=False),
        sa.Column("position_token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.INTEGER(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("liquidity", sa.NUMERIC(precision=78), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("period_date", "position_token_address", "token_id"),
    )
    op.create_index(
        "af_uniswap_v3_token_data_period_date_index", "af_uniswap_v3_token_data_period", ["period_date"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("af_uniswap_v3_token_data_period_date_index", table_name="af_uniswap_v3_token_data_period")
    op.drop_table("af_uniswap_v3_token_data_period")
    op.drop_index("af_uniswap_v3_token_data_daily_index", table_name="af_uniswap_v3_token_data_daily")
    op.drop_table("af_uniswap_v3_token_data_daily")
    op.drop_index("af_uniswap_v3_pool_prices_period_period_date_index", table_name="af_uniswap_v3_pool_prices_period")
    op.drop_table("af_uniswap_v3_pool_prices_period")
    op.drop_index("af_uniswap_v3_pool_prices_daily_block_date_index", table_name="af_uniswap_v3_pool_prices_daily")
    op.drop_table("af_uniswap_v3_pool_prices_daily")
    op.drop_table("af_merchant_moe_token_bin_hist_period")
    op.drop_index("af_holding_balance_uniswap_v3_period_period_date", table_name="af_holding_balance_uniswap_v3_period")
    op.drop_table("af_holding_balance_uniswap_v3_period")
    op.drop_index(
        "af_holding_balance_merchantmoe_period_period_date", table_name="af_holding_balance_merchantmoe_period"
    )
    op.drop_table("af_holding_balance_merchantmoe_period")
    # ### end Alembic commands ###
