"""add address_token_deposit table

Revision ID: 6c2eecd6316b
Revises: 2359a28d63cb
Create Date: 2024-08-30 15:09:43.357835

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6c2eecd6316b"
down_revision: Union[str, None] = "2359a28d63cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "af_token_deposits__transactions",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=True),
        sa.Column("chain_id", sa.BIGINT(), nullable=True),
        sa.Column("contract_address", postgresql.BYTEA(), nullable=True),
        sa.Column("token_address", postgresql.BYTEA(), nullable=True),
        sa.Column("value", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("transaction_hash"),
    )
    op.create_index(
        "af_deposits_transactions_block_number_index",
        "af_token_deposits__transactions",
        [sa.text("block_number DESC")],
        unique=False,
    )
    op.create_index(
        "af_deposits_transactions_chain_id_index", "af_token_deposits__transactions", ["chain_id"], unique=False
    )
    op.create_index(
        "af_deposits_transactions_contract_address_index",
        "af_token_deposits__transactions",
        ["contract_address"],
        unique=False,
    )
    op.create_index(
        "af_deposits_transactions_token_address_index",
        "af_token_deposits__transactions",
        ["token_address"],
        unique=False,
    )
    op.create_index(
        "af_deposits_transactions_wallet_address_index",
        "af_token_deposits__transactions",
        ["wallet_address"],
        unique=False,
    )
    op.create_table(
        "af_token_deposits_current",
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("chain_id", sa.BIGINT(), nullable=False),
        sa.Column("contract_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("value", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("wallet_address", "token_address", "contract_address", "chain_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("af_deposits_transactions_wallet_address_index", table_name="af_token_deposits__transactions")
    op.drop_index("af_deposits_transactions_token_address_index", table_name="af_token_deposits__transactions")
    op.drop_index("af_deposits_transactions_contract_address_index", table_name="af_token_deposits__transactions")
    op.drop_index("af_deposits_transactions_chain_id_index", table_name="af_token_deposits__transactions")
    op.drop_index("af_deposits_transactions_block_number_index", table_name="af_token_deposits__transactions")
    op.drop_table("af_token_deposits_current")
    op.drop_table("af_token_deposits__transactions")
    # ### end Alembic commands ###
