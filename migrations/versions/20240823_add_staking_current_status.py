"""add staking current status

Revision ID: 5793b33b3f4c
Revises: 9769e538c63f
Create Date: 2024-08-23 17:05:32.595105

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5793b33b3f4c"
down_revision: Union[str, None] = "9769e538c63f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_staked_fbtc_status",
        sa.Column("contract_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("amount", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("protocol_id", sa.VARCHAR(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("contract_address", "wallet_address"),
    )
    op.create_index(
        "feature_staked_fbtc_status_protocol_block_desc_index",
        "feature_staked_fbtc_status",
        [sa.text("protocol_id DESC")],
        unique=False,
    )
    op.create_index(
        "feature_staked_fbtc_status_wallet_block_desc_index",
        "feature_staked_fbtc_status",
        [sa.text("wallet_address DESC")],
        unique=False,
    )
    op.drop_column("feature_staked_fbtc_detail_records", "log_index")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "feature_staked_fbtc_detail_records", sa.Column("log_index", sa.BIGINT(), autoincrement=False, nullable=False)
    )
    op.drop_index("feature_staked_fbtc_status_wallet_block_desc_index", table_name="feature_staked_fbtc_status")
    op.drop_index("feature_staked_fbtc_status_protocol_block_desc_index", table_name="feature_staked_fbtc_status")
    op.drop_table("feature_staked_fbtc_status")
    # ### end Alembic commands ###
