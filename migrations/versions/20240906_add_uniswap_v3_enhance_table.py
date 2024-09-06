"""add uniswap v3 enhance table

Revision ID: f4efa18760cc
Revises: 2359a28d63cb
Create Date: 2024-09-06 13:24:28.201489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4efa18760cc'
down_revision: Union[str, None] = '2359a28d63cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    op.create_table('af_uniswap_v3_pool_prices_current',
    sa.Column('pool_address', postgresql.BYTEA(), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=True),
    sa.Column('factory_address', postgresql.BYTEA(), nullable=True),
    sa.Column('sqrt_price_x96', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('tick', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('pool_address')
    )
    op.create_table('af_uniswap_v3_pool_prices_hist',
    sa.Column('pool_address', postgresql.BYTEA(), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=False),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=False),
    sa.Column('sqrt_price_x96', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('tick', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('factory_address', postgresql.BYTEA(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('reorg', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('pool_address', 'block_timestamp', 'block_number')
    )
    op.create_table('af_uniswap_v3_pool_swap_hist',
    sa.Column('pool_address', postgresql.BYTEA(), nullable=False),
    sa.Column('transaction_hash', postgresql.BYTEA(), nullable=False),
    sa.Column('log_index', sa.INTEGER(), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=True),
    sa.Column('nft_address', postgresql.BYTEA(), nullable=True),
    sa.Column('transaction_from_address', postgresql.BYTEA(), nullable=True),
    sa.Column('sender', postgresql.BYTEA(), nullable=True),
    sa.Column('recipient', postgresql.BYTEA(), nullable=True),
    sa.Column('liquidity', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('tick', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('sqrt_price_x96', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('amount0', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('amount1', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('token0_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token1_address', postgresql.BYTEA(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('reorg', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('pool_address', 'transaction_hash', 'log_index')
    )
    op.create_table('af_uniswap_v3_pools',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=False),
    sa.Column('factory_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token0_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token1_address', postgresql.BYTEA(), nullable=True),
    sa.Column('fee', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('tick_spacing', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'pool_address')
    )
    op.create_table('af_uniswap_v3_token_collect_fee_hist',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=False),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=False),
    sa.Column('log_index', sa.INTEGER(), nullable=False),
    sa.Column('transaction_hash', postgresql.BYTEA(), nullable=True),
    sa.Column('owner', postgresql.BYTEA(), nullable=True),
    sa.Column('recipient', postgresql.BYTEA(), nullable=True),
    sa.Column('amount0', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('amount1', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token0_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token1_address', postgresql.BYTEA(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('reorg', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id', 'block_timestamp', 'block_number', 'log_index')
    )
    op.create_index('af_uniswap_v3_token_collect_fee_hist_owner_index', 'af_uniswap_v3_token_collect_fee_hist', ['owner'], unique=False)
    op.create_index('af_uniswap_v3_token_collect_fee_hist_pool_index', 'af_uniswap_v3_token_collect_fee_hist', ['pool_address'], unique=False)
    op.create_index('af_uniswap_v3_token_collect_fee_hist_token0_index', 'af_uniswap_v3_token_collect_fee_hist', ['token0_address'], unique=False)
    op.create_index('af_uniswap_v3_token_collect_fee_hist_token1_index', 'af_uniswap_v3_token_collect_fee_hist', ['token1_address'], unique=False)
    op.create_index('af_uniswap_v3_token_collect_fee_hist_token_id_index', 'af_uniswap_v3_token_collect_fee_hist', ['token_id'], unique=False)
    op.create_table('af_uniswap_v3_token_data_current',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=True),
    sa.Column('wallet_address', postgresql.BYTEA(), nullable=True),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=True),
    sa.Column('liquidity', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id')
    )
    op.create_index('af_uniswap_v3_token_data_current_wallet_desc_index', 'af_uniswap_v3_token_data_current', [sa.text('wallet_address DESC')], unique=False)
    op.create_table('af_uniswap_v3_token_data_hist',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=False),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=False),
    sa.Column('wallet_address', postgresql.BYTEA(), nullable=True),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=True),
    sa.Column('liquidity', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('reorg', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id', 'block_timestamp', 'block_number')
    )
    op.create_index('af_uniswap_v3_token_data_hist_token_block_desc_index', 'af_uniswap_v3_token_data_hist', [sa.text('nft_address DESC'), sa.text('block_timestamp DESC')], unique=False)
    op.create_index('af_uniswap_v3_token_data_hist_wallet_token_block_desc_index', 'af_uniswap_v3_token_data_hist', [sa.text('wallet_address DESC'), sa.text('nft_address DESC'), sa.text('block_timestamp DESC')], unique=False)
    op.create_table('af_uniswap_v3_token_liquidity_hist',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100), nullable=False),
    sa.Column('block_number', sa.BIGINT(), nullable=False),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=False),
    sa.Column('log_index', sa.INTEGER(), nullable=False),
    sa.Column('transaction_hash', postgresql.BYTEA(), nullable=True),
    sa.Column('owner', postgresql.BYTEA(), nullable=True),
    sa.Column('liquidity', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('amount0', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('amount1', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token0_address', postgresql.BYTEA(), nullable=True),
    sa.Column('token1_address', postgresql.BYTEA(), nullable=True),
    sa.Column('action_type', sa.VARCHAR(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('reorg', sa.BOOLEAN(), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id', 'block_timestamp', 'block_number', 'log_index')
    )
    op.create_index('af_uniswap_v3_token_liquidity_hist_owner_index', 'af_uniswap_v3_token_liquidity_hist', ['owner'], unique=False)
    op.create_index('af_uniswap_v3_token_liquidity_hist_pool_index', 'af_uniswap_v3_token_liquidity_hist', ['pool_address'], unique=False)
    op.create_index('af_uniswap_v3_token_liquidity_hist_token0_index', 'af_uniswap_v3_token_liquidity_hist', ['token0_address'], unique=False)
    op.create_index('af_uniswap_v3_token_liquidity_hist_token1_index', 'af_uniswap_v3_token_liquidity_hist', ['token1_address'], unique=False)
    op.create_index('af_uniswap_v3_token_liquidity_hist_token_id_index', 'af_uniswap_v3_token_liquidity_hist', ['token_id'], unique=False)
    op.create_table('af_uniswap_v3_tokens',
    sa.Column('nft_address', postgresql.BYTEA(), nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100), nullable=False),
    sa.Column('pool_address', postgresql.BYTEA(), nullable=True),
    sa.Column('tick_lower', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('tick_upper', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('fee', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_timestamp', sa.BIGINT(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id')
    )
    op.create_index('af_uniswap_v3_tokens_nft_index', 'af_uniswap_v3_tokens', ['nft_address'], unique=False)
    op.drop_index('feature_uniswap_v3_tokens_nft_index', table_name='feature_uniswap_v3_tokens')
    op.drop_table('feature_uniswap_v3_tokens')
    op.drop_table('feature_uniswap_v3_pools')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('feature_uniswap_v3_pools',
    sa.Column('nft_address', postgresql.BYTEA(), autoincrement=False, nullable=False),
    sa.Column('pool_address', postgresql.BYTEA(), autoincrement=False, nullable=False),
    sa.Column('token0_address', postgresql.BYTEA(), autoincrement=False, nullable=True),
    sa.Column('token1_address', postgresql.BYTEA(), autoincrement=False, nullable=True),
    sa.Column('fee', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=True),
    sa.Column('tick_spacing', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('called_block_number', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'pool_address', name='feature_uniswap_v3_pools_pkey')
    )
    op.create_table('feature_uniswap_v3_tokens',
    sa.Column('nft_address', postgresql.BYTEA(), autoincrement=False, nullable=False),
    sa.Column('token_id', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=False),
    sa.Column('pool_address', postgresql.BYTEA(), autoincrement=False, nullable=True),
    sa.Column('tick_lower', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=True),
    sa.Column('tick_upper', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=True),
    sa.Column('fee', sa.NUMERIC(precision=100, scale=0), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('called_block_number', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('nft_address', 'token_id', name='feature_uniswap_v3_tokens_pkey')
    )
    op.create_index('feature_uniswap_v3_tokens_nft_index', 'feature_uniswap_v3_tokens', ['nft_address'], unique=False)

    op.drop_index('af_uniswap_v3_tokens_nft_index', table_name='af_uniswap_v3_tokens')
    op.drop_table('af_uniswap_v3_tokens')
    op.drop_index('af_uniswap_v3_token_liquidity_hist_token_id_index', table_name='af_uniswap_v3_token_liquidity_hist')
    op.drop_index('af_uniswap_v3_token_liquidity_hist_token1_index', table_name='af_uniswap_v3_token_liquidity_hist')
    op.drop_index('af_uniswap_v3_token_liquidity_hist_token0_index', table_name='af_uniswap_v3_token_liquidity_hist')
    op.drop_index('af_uniswap_v3_token_liquidity_hist_pool_index', table_name='af_uniswap_v3_token_liquidity_hist')
    op.drop_index('af_uniswap_v3_token_liquidity_hist_owner_index', table_name='af_uniswap_v3_token_liquidity_hist')
    op.drop_table('af_uniswap_v3_token_liquidity_hist')
    op.drop_index('af_uniswap_v3_token_data_hist_wallet_token_block_desc_index', table_name='af_uniswap_v3_token_data_hist')
    op.drop_index('af_uniswap_v3_token_data_hist_token_block_desc_index', table_name='af_uniswap_v3_token_data_hist')
    op.drop_table('af_uniswap_v3_token_data_hist')
    op.drop_index('af_uniswap_v3_token_data_current_wallet_desc_index', table_name='af_uniswap_v3_token_data_current')
    op.drop_table('af_uniswap_v3_token_data_current')
    op.drop_index('af_uniswap_v3_token_collect_fee_hist_token_id_index', table_name='af_uniswap_v3_token_collect_fee_hist')
    op.drop_index('af_uniswap_v3_token_collect_fee_hist_token1_index', table_name='af_uniswap_v3_token_collect_fee_hist')
    op.drop_index('af_uniswap_v3_token_collect_fee_hist_token0_index', table_name='af_uniswap_v3_token_collect_fee_hist')
    op.drop_index('af_uniswap_v3_token_collect_fee_hist_pool_index', table_name='af_uniswap_v3_token_collect_fee_hist')
    op.drop_index('af_uniswap_v3_token_collect_fee_hist_owner_index', table_name='af_uniswap_v3_token_collect_fee_hist')
    op.drop_table('af_uniswap_v3_token_collect_fee_hist')
    op.drop_table('af_uniswap_v3_pools')
    op.drop_table('af_uniswap_v3_pool_swap_hist')
    op.drop_table('af_uniswap_v3_pool_prices_hist')
    op.drop_table('af_uniswap_v3_pool_prices_current')
    # ### end Alembic commands ###
