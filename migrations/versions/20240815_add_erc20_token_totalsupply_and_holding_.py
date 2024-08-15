"""add erc20_token totalSupply and holding feature

Revision ID: 09174034ce4d
Revises: bf51d23c852f
Create Date: 2024-08-15 14:54:37.640464

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "09174034ce4d"
down_revision: Union[str, None] = "bf51d23c852f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_erc20_token_holding",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("called_block_number", sa.BIGINT(), nullable=False),
        sa.Column("called_block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "wallet_address", "called_block_timestamp", "called_block_number"),
    )
    op.create_index(
        "feature_erc20_token_holding_token_block_desc_index",
        "feature_erc20_token_holding",
        [sa.text("token_address DESC"), sa.text("called_block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_erc20_token_holding_token_wallet_block_desc_index",
        "feature_erc20_token_holding",
        [sa.text("token_address DESC"), sa.text("wallet_address DESC"), sa.text("called_block_number DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc20_total_supply",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("called_block_number", sa.BIGINT(), nullable=False),
        sa.Column("called_block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("total_supply", sa.BIGINT(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "called_block_timestamp", "called_block_number"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("feature_erc20_total_supply")
    op.drop_index("feature_erc20_token_holding_token_wallet_block_desc_index", table_name="feature_erc20_token_holding")
    op.drop_index("feature_erc20_token_holding_token_block_desc_index", table_name="feature_erc20_token_holding")
    op.drop_table("feature_erc20_token_holding")
    # ### end Alembic commands ###
