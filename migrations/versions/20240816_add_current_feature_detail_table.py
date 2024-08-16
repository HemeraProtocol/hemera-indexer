"""add current feature detail table

Revision ID: dec78d700d1c
Revises: 87ebc3fcd9ca
Create Date: 2024-08-16 18:33:10.794073

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dec78d700d1c"
down_revision: Union[str, None] = "87ebc3fcd9ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_erc20_current_token_holdings",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("wallet_address", "token_address"),
    )
    op.create_index(
        "feature_erc20_current_token_holdings_token_balance_index",
        "feature_erc20_current_token_holdings",
        ["token_address", sa.text("balance DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc20_current_total_supply_records",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("total_supply", sa.BIGINT(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address"),
    )
    op.create_table(
        "feature_uniswap_v3_pool_current_prices",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address"),
    )
    op.create_table(
        "feature_uniswap_v3_token_current_status",
        sa.Column("nft_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=True),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=True),
        sa.Column("liquidity", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("nft_address", "token_id"),
    )
    op.create_index(
        "feature_uniswap_v3_token_current_status_wallet_desc_index",
        "feature_uniswap_v3_token_current_status",
        [sa.text("wallet_address DESC")],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "feature_uniswap_v3_token_current_status_wallet_desc_index",
        table_name="feature_uniswap_v3_token_current_status",
    )
    op.drop_table("feature_uniswap_v3_token_current_status")
    op.drop_table("feature_uniswap_v3_pool_current_prices")
    op.drop_table("feature_erc20_current_total_supply_records")
    op.drop_index(
        "feature_erc20_current_token_holdings_token_balance_index", table_name="feature_erc20_current_token_holdings"
    )
    op.drop_table("feature_erc20_current_token_holdings")
    # ### end Alembic commands ###
