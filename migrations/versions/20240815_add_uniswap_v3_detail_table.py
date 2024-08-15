"""add uniswap v3 detail table

Revision ID: 2961c81d0b50
Revises: 09174034ce4d
Create Date: 2024-08-15 18:36:23.720961

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2961c81d0b50"
down_revision: Union[str, None] = "09174034ce4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_uniswap_v3_pool_prices",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("called_block_number", sa.BIGINT(), nullable=False),
        sa.Column("called_block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address", "called_block_timestamp", "called_block_number"),
    )
    op.create_table(
        "feature_uniswap_v3_token_details",
        sa.Column("nft_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("called_block_number", sa.BIGINT(), nullable=False),
        sa.Column("called_block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=True),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=True),
        sa.Column("liquidity", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("nft_address", "token_id", "called_block_timestamp", "called_block_number"),
    )
    op.create_index(
        "feature_uniswap_v3_token_details_token_block_desc_index",
        "feature_uniswap_v3_token_details",
        [sa.text("nft_address DESC"), sa.text("called_block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_uniswap_v3_token_details_wallet_token_block_desc_index",
        "feature_uniswap_v3_token_details",
        [sa.text("wallet_address DESC"), sa.text("nft_address DESC"), sa.text("called_block_timestamp DESC")],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "feature_uniswap_v3_token_details_wallet_token_block_desc_index", table_name="feature_uniswap_v3_token_details"
    )
    op.drop_index(
        "feature_uniswap_v3_token_details_token_block_desc_index", table_name="feature_uniswap_v3_token_details"
    )
    op.drop_table("feature_uniswap_v3_token_details")
    op.drop_table("feature_uniswap_v3_pool_prices")
    # ### end Alembic commands ###
