"""ens

Revision ID: 43d14640a8ac
Revises: 6c2eecd6316b
Create Date: 2024-09-05 11:08:15.501786

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "43d14640a8ac"
down_revision: Union[str, None] = "6c2eecd6316b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "af_ens_address_current",
        sa.Column("address", postgresql.BYTEA(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("reverse_node", postgresql.BYTEA(), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("create_time", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("address"),
    )
    op.create_table(
        "af_ens_event",
        sa.Column("transaction_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("transaction_index", sa.Integer(), nullable=True),
        sa.Column("log_index", sa.Integer(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_hash", postgresql.BYTEA(), nullable=True),
        sa.Column("block_timestamp", sa.TIMESTAMP(), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("event_name", sa.String(), nullable=True),
        sa.Column("topic0", sa.String(), nullable=True),
        sa.Column("from_address", postgresql.BYTEA(), nullable=True),
        sa.Column("to_address", postgresql.BYTEA(), nullable=True),
        sa.Column("base_node", postgresql.BYTEA(), nullable=True),
        sa.Column("node", postgresql.BYTEA(), nullable=True),
        sa.Column("label", postgresql.BYTEA(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("expires", sa.TIMESTAMP(), nullable=True),
        sa.Column("owner", postgresql.BYTEA(), nullable=True),
        sa.Column("resolver", postgresql.BYTEA(), nullable=True),
        sa.Column("registrant", postgresql.BYTEA(), nullable=True),
        sa.Column("address", postgresql.BYTEA(), nullable=True),
        sa.Column("reverse_base_node", postgresql.BYTEA(), nullable=True),
        sa.Column("reverse_node", postgresql.BYTEA(), nullable=True),
        sa.Column("reverse_label", postgresql.BYTEA(), nullable=True),
        sa.Column("reverse_name", sa.String(), nullable=True),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("w_token_id", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("transaction_hash", "log_index", name="ens_tnx_log_index"),
    )
    op.create_index("ens_event_address", "af_ens_event", ["from_address"], unique=False)
    op.create_index(
        "ens_idx_block_number_log_index", "af_ens_event", ["block_number", sa.text("log_index DESC")], unique=False
    )
    op.create_table(
        "af_ens_node_current",
        sa.Column("node", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("w_token_id", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("first_owned_by", postgresql.BYTEA(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("registration", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("expires", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("address", postgresql.BYTEA(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("node"),
        sa.UniqueConstraint("node"),
    )
    op.create_index("ens_idx_address", "af_ens_node_current", ["address"], unique=False)
    op.create_index("ens_idx_name", "af_ens_node_current", ["name"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ens_idx_name", table_name="af_ens_node_current")
    op.drop_index("ens_idx_address", table_name="af_ens_node_current")
    op.drop_table("af_ens_node_current")
    op.drop_index("ens_idx_block_number_log_index", table_name="af_ens_event")
    op.drop_index("ens_event_address", table_name="af_ens_event")
    op.drop_table("af_ens_event")
    op.drop_table("af_ens_address_current")
    # ### end Alembic commands ###
