"""tokens table add column 'update_block_number'

Revision ID: 8a915490914a
Revises: 5e4608933f64
Create Date: 2024-07-08 21:57:41.134980

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a915490914a"
down_revision: Union[str, None] = "5e4608933f64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("tokens", sa.Column("update_block_number", sa.BIGINT(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tokens", "update_block_number")
    # ### end Alembic commands ###
