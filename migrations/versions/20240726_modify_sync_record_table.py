"""modify sync_record table

Revision ID: 0b922153e040
Revises: 9f2cf385645f
Create Date: 2024-07-26 19:35:46.987343

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0b922153e040"
down_revision: Union[str, None] = "9f2cf385645f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("sync_record")
    op.create_table(
        "sync_record",
        sa.Column("mission_sign", sa.VARCHAR(), nullable=False),
        sa.Column("last_block_number", sa.BIGINT(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("mission_sign"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("sync_record")
    op.create_table(
        "sync_record",
        sa.Column("mission_type", sa.VARCHAR(), nullable=False),
        sa.Column("entity_types", sa.INTEGER(), nullable=False),
        sa.Column("last_block_number", sa.BIGINT(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("mission_type", "entity_types"),
    )
    # ### end Alembic commands ###
