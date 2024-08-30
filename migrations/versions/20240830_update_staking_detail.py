"""update detail

Revision ID: 5a7a24fc464b
Revises: 0043891d8824
Create Date: 2024-08-30 16:14:16.785371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a7a24fc464b'
down_revision: Union[str, None] = '0043891d8824'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('feature_staked_fbtc_status', 'block_number',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('feature_staked_fbtc_status', 'block_timestamp',
               existing_type=sa.BIGINT(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('feature_staked_fbtc_status', 'block_timestamp',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('feature_staked_fbtc_status', 'block_number',
               existing_type=sa.BIGINT(),
               nullable=False)
    # ### end Alembic commands ###
