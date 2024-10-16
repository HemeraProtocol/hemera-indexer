"""add uniswap v2 table

Revision ID: aa99dd347ef1
Revises: e3a3e2114b9c
Create Date: 2024-08-02 16:17:43.105236

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "aa99dd347ef1"
down_revision: Union[str, None] = "e3a3e2114b9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_uniswap_v2_pools",
        sa.Column("factory_address", postgresql.BYTEA(), nullable=False),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token0_address", postgresql.BYTEA(), nullable=True),
        sa.Column("token1_address", postgresql.BYTEA(), nullable=True),
        sa.Column("length", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("called_block_number", sa.BIGINT(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("factory_address", "pool_address"),
    )
    op.add_column("feature_uniswap_v3_pools", sa.Column("called_block_number", sa.BIGINT(), nullable=True))
    op.drop_column("feature_uniswap_v3_pools", "mint_block_number")
    op.add_column("feature_uniswap_v3_tokens", sa.Column("called_block_number", sa.BIGINT(), nullable=True))
    op.drop_column("feature_uniswap_v3_tokens", "mint_block_number")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "feature_uniswap_v3_tokens", sa.Column("mint_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_uniswap_v3_tokens", "called_block_number")
    op.add_column(
        "feature_uniswap_v3_pools", sa.Column("mint_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_uniswap_v3_pools", "called_block_number")
    op.drop_table("feature_uniswap_v2_pools")
    # ### end Alembic commands ###
