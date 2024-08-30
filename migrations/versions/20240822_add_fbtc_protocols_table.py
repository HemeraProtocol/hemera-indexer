"""add fbtc protocols table

Revision ID: 8ed65fe65ee5
Revises: bf51d23c852f
Create Date: 2024-08-22 18:17:17.361251

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8ed65fe65ee5"
down_revision: Union[str, None] = "bf51d23c852f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "feature_erc1155_token_current_holdings",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id", "wallet_address"),
    )
    op.create_index(
        "feature_erc1155_token_current_holdings_token_block_desc_index",
        "feature_erc1155_token_current_holdings",
        [sa.text("token_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_erc1155_token_current_holdings_wallet_block_desc_index",
        "feature_erc1155_token_current_holdings",
        [sa.text("wallet_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc1155_token_current_supply_status",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id"),
    )
    op.create_table(
        "feature_erc1155_token_holdings",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id", "wallet_address", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_erc1155_token_holding_token_block_desc_index",
        "feature_erc1155_token_holdings",
        [sa.text("token_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_erc1155_token_holding_token_wallet_block_desc_index",
        "feature_erc1155_token_holdings",
        [sa.text("token_address DESC"), sa.text("wallet_address DESC"), sa.text("block_number DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc1155_token_supply_records",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_erc1155_token_supply_token_block_desc_index",
        "feature_erc1155_token_supply_records",
        [sa.text("token_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc20_current_token_holdings",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("wallet_address", "token_address"),
    )
    op.create_index(
        "feature_erc20_current_token_holdings_token_balance_index",
        "feature_erc20_current_token_holdings",
        ["token_address", sa.text("balance DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc20_current_total_supply_records",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address"),
    )
    op.create_table(
        "feature_erc20_token_holdings",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "wallet_address", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_erc20_token_holdings_token_block_desc_index",
        "feature_erc20_token_holdings",
        [sa.text("token_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_erc20_token_holdings_token_wallet_block_desc_index",
        "feature_erc20_token_holdings",
        [sa.text("token_address DESC"), sa.text("wallet_address DESC"), sa.text("block_number DESC")],
        unique=False,
    )
    op.create_table(
        "feature_erc20_total_supply_records",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "block_timestamp", "block_number"),
    )
    op.create_table(
        "feature_merchant_moe_token_bin_current_status",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("reserve0_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("reserve1_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id"),
    )
    op.create_index(
        "feature_merchant_moe_token_bin_current_status_token_id_index",
        "feature_merchant_moe_token_bin_current_status",
        [sa.text("token_address DESC"), sa.text("token_id ASC")],
        unique=False,
    )
    op.create_table(
        "feature_merchant_moe_token_bin_records",
        sa.Column("token_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("reserve0_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("reserve1_bin", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("token_address", "token_id", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_merchant_moe_token_bin_records_token_block_desc_index",
        "feature_merchant_moe_token_bin_records",
        [sa.text("token_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_table(
        "feature_staked_fbtc_detail_records",
        sa.Column("contract_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("log_index", sa.BIGINT(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("amount", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("protocol_id", sa.VARCHAR(), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("contract_address", "wallet_address", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_staked_fbtc_detail_records_protocol_block_desc_index",
        "feature_staked_fbtc_detail_records",
        [sa.text("protocol_id DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_staked_fbtc_detail_records_wallet_block_desc_index",
        "feature_staked_fbtc_detail_records",
        [sa.text("wallet_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_table(
        "feature_uniswap_v2_liquidity_current_holdings",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("wallet_address", "pool_address"),
    )
    op.create_index(
        "feature_uniswap_v2_liquidity_current_holdings_balance_index",
        "feature_uniswap_v2_liquidity_current_holdings",
        ["pool_address", sa.text("balance DESC")],
        unique=False,
    )
    op.create_table(
        "feature_uniswap_v2_liquidity_holding_records",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("balance", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address", "wallet_address", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_uniswap_v2_liquidity_holding_records_pool_b_dindex",
        "feature_uniswap_v2_liquidity_holding_records",
        [sa.text("pool_address DESC"), sa.text("block_number DESC")],
        unique=False,
    )
    op.create_index(
        "feature_uniswap_v2_liquidity_holding_records_wallet_b_dindex",
        "feature_uniswap_v2_liquidity_holding_records",
        [sa.text("pool_address DESC"), sa.text("wallet_address DESC"), sa.text("block_number DESC")],
        unique=False,
    )
    op.create_table(
        "feature_uniswap_v2_pool_current_reserves",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("reserve0", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("reserve1", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("block_timestamp_last", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address"),
    )
    op.create_table(
        "feature_uniswap_v2_pool_reserves_records",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("reserve0", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("reserve1", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("block_timestamp_last", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),
    )
    op.create_table(
        "feature_uniswap_v2_pool_total_supply_records",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),
    )
    op.create_table(
        "feature_uniswap_v2_pools_current_total_supply",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("total_supply", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address"),
    )
    op.create_table(
        "feature_uniswap_v3_pool_current_prices",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address"),
    )
    op.create_table(
        "feature_uniswap_v3_pool_prices",
        sa.Column("pool_address", postgresql.BYTEA(), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("sqrt_price_x96", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),
    )
    op.create_table(
        "feature_uniswap_v3_token_current_status",
        sa.Column("nft_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=True),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=True),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=True),
        sa.Column("liquidity", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("nft_address", "token_id"),
    )
    op.create_index(
        "feature_uniswap_v3_token_current_status_wallet_desc_index",
        "feature_uniswap_v3_token_current_status",
        [sa.text("wallet_address DESC")],
        unique=False,
    )
    op.create_table(
        "feature_uniswap_v3_token_details",
        sa.Column("nft_address", postgresql.BYTEA(), nullable=False),
        sa.Column("token_id", sa.NUMERIC(precision=100), nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=False),
        sa.Column("block_timestamp", sa.BIGINT(), nullable=False),
        sa.Column("wallet_address", postgresql.BYTEA(), nullable=True),
        sa.Column("pool_address", postgresql.BYTEA(), nullable=True),
        sa.Column("liquidity", sa.NUMERIC(precision=100), nullable=True),
        sa.Column("create_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("update_time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("reorg", sa.BOOLEAN(), nullable=True),
        sa.PrimaryKeyConstraint("nft_address", "token_id", "block_timestamp", "block_number"),
    )
    op.create_index(
        "feature_uniswap_v3_token_details_token_block_desc_index",
        "feature_uniswap_v3_token_details",
        [sa.text("nft_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "feature_uniswap_v3_token_details_wallet_token_block_desc_index",
        "feature_uniswap_v3_token_details",
        [sa.text("wallet_address DESC"), sa.text("nft_address DESC"), sa.text("block_timestamp DESC")],
        unique=False,
    )
    op.add_column("feature_blue_chip_holders", sa.Column("block_number", sa.BIGINT(), nullable=True))
    op.add_column("feature_blue_chip_holders", sa.Column("block_timestamp", postgresql.TIMESTAMP(), nullable=True))
    op.drop_column("feature_blue_chip_holders", "called_block_number")
    op.drop_column("feature_blue_chip_holders", "called_block_timestamp")
    op.add_column("feature_uniswap_v2_pools", sa.Column("block_number", sa.BIGINT(), nullable=True))
    op.drop_column("feature_uniswap_v2_pools", "called_block_number")
    op.add_column("feature_uniswap_v3_pools", sa.Column("block_number", sa.BIGINT(), nullable=True))
    op.drop_column("feature_uniswap_v3_pools", "called_block_number")
    op.add_column("feature_uniswap_v3_tokens", sa.Column("block_number", sa.BIGINT(), nullable=True))
    op.drop_column("feature_uniswap_v3_tokens", "called_block_number")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "feature_uniswap_v3_tokens", sa.Column("called_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_uniswap_v3_tokens", "block_number")
    op.add_column(
        "feature_uniswap_v3_pools", sa.Column("called_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_uniswap_v3_pools", "block_number")
    op.add_column(
        "feature_uniswap_v2_pools", sa.Column("called_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_uniswap_v2_pools", "block_number")
    op.add_column(
        "feature_blue_chip_holders",
        sa.Column("called_block_timestamp", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "feature_blue_chip_holders", sa.Column("called_block_number", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.drop_column("feature_blue_chip_holders", "block_timestamp")
    op.drop_column("feature_blue_chip_holders", "block_number")
    op.drop_table("token_address_nft_inventories")
    op.drop_index(
        "feature_uniswap_v3_token_details_wallet_token_block_desc_index", table_name="feature_uniswap_v3_token_details"
    )
    op.drop_index(
        "feature_uniswap_v3_token_details_token_block_desc_index", table_name="feature_uniswap_v3_token_details"
    )
    op.drop_table("feature_uniswap_v3_token_details")
    op.drop_index(
        "feature_uniswap_v3_token_current_status_wallet_desc_index",
        table_name="feature_uniswap_v3_token_current_status",
    )
    op.drop_table("feature_uniswap_v3_token_current_status")
    op.drop_table("feature_uniswap_v3_pool_prices")
    op.drop_table("feature_uniswap_v3_pool_current_prices")
    op.drop_table("feature_uniswap_v2_pools_current_total_supply")
    op.drop_table("feature_uniswap_v2_pool_total_supply_records")
    op.drop_table("feature_uniswap_v2_pool_reserves_records")
    op.drop_table("feature_uniswap_v2_pool_current_reserves")
    op.drop_index(
        "feature_uniswap_v2_liquidity_holding_records_wallet_b_dindex",
        table_name="feature_uniswap_v2_liquidity_holding_records",
    )
    op.drop_index(
        "feature_uniswap_v2_liquidity_holding_records_pool_b_dindex",
        table_name="feature_uniswap_v2_liquidity_holding_records",
    )
    op.drop_table("feature_uniswap_v2_liquidity_holding_records")
    op.drop_index(
        "feature_uniswap_v2_liquidity_current_holdings_balance_index",
        table_name="feature_uniswap_v2_liquidity_current_holdings",
    )
    op.drop_table("feature_uniswap_v2_liquidity_current_holdings")
    op.drop_index(
        "feature_staked_fbtc_detail_records_wallet_block_desc_index", table_name="feature_staked_fbtc_detail_records"
    )
    op.drop_index(
        "feature_staked_fbtc_detail_records_protocol_block_desc_index", table_name="feature_staked_fbtc_detail_records"
    )
    op.drop_table("feature_staked_fbtc_detail_records")
    op.drop_index(
        "feature_merchant_moe_token_bin_records_token_block_desc_index",
        table_name="feature_merchant_moe_token_bin_records",
    )
    op.drop_table("feature_merchant_moe_token_bin_records")
    op.drop_index(
        "feature_merchant_moe_token_bin_current_status_token_id_index",
        table_name="feature_merchant_moe_token_bin_current_status",
    )
    op.drop_table("feature_merchant_moe_token_bin_current_status")
    op.drop_table("feature_erc20_total_supply_records")
    op.drop_index(
        "feature_erc20_token_holdings_token_wallet_block_desc_index", table_name="feature_erc20_token_holdings"
    )
    op.drop_index("feature_erc20_token_holdings_token_block_desc_index", table_name="feature_erc20_token_holdings")
    op.drop_table("feature_erc20_token_holdings")
    op.drop_table("feature_erc20_current_total_supply_records")
    op.drop_index(
        "feature_erc20_current_token_holdings_token_balance_index", table_name="feature_erc20_current_token_holdings"
    )
    op.drop_table("feature_erc20_current_token_holdings")
    op.drop_index(
        "feature_erc1155_token_supply_token_block_desc_index", table_name="feature_erc1155_token_supply_records"
    )
    op.drop_table("feature_erc1155_token_supply_records")
    op.drop_index(
        "feature_erc1155_token_holding_token_wallet_block_desc_index", table_name="feature_erc1155_token_holdings"
    )
    op.drop_index("feature_erc1155_token_holding_token_block_desc_index", table_name="feature_erc1155_token_holdings")
    op.drop_table("feature_erc1155_token_holdings")
    op.drop_table("feature_erc1155_token_current_supply_status")
    op.drop_index(
        "feature_erc1155_token_current_holdings_wallet_block_desc_index",
        table_name="feature_erc1155_token_current_holdings",
    )
    op.drop_index(
        "feature_erc1155_token_current_holdings_token_block_desc_index",
        table_name="feature_erc1155_token_current_holdings",
    )
    op.drop_table("feature_erc1155_token_current_holdings")
    # ### end Alembic commands ###
