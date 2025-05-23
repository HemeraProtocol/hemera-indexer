BEGIN;

-- Running upgrade 3dd9b90d2e31 -> c609922eae7a

CREATE TABLE IF NOT EXISTS af_merchant_moe_pools (
    position_token_address BYTEA NOT NULL,
    block_timestamp BIGINT,
    block_number BIGINT,
    token0_address BYTEA,
    token1_address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address)
);

CREATE TABLE IF NOT EXISTS af_merchant_moe_token_bin_current (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_timestamp BIGINT,
    block_number BIGINT,
    reserve0_bin NUMERIC(100),
    reserve1_bin NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, token_id)
);

CREATE INDEX af_merchant_moe_token_bin_current_token_id_index ON af_merchant_moe_token_bin_current (position_token_address DESC, token_id ASC);

CREATE TABLE IF NOT EXISTS af_merchant_moe_token_bin_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_timestamp BIGINT NOT NULL,
    block_number BIGINT NOT NULL,
    reserve0_bin NUMERIC(100),
    reserve1_bin NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address, token_id, block_timestamp, block_number)
);

CREATE INDEX af_merchant_moe_token_bin_hist_token_block_desc_index ON af_merchant_moe_token_bin_hist (position_token_address DESC, block_timestamp DESC);

CREATE TABLE IF NOT EXISTS af_merchant_moe_token_supply_current (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_timestamp BIGINT,
    block_number BIGINT,
    total_supply NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, token_id)
);

CREATE TABLE IF NOT EXISTS af_merchant_moe_token_supply_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_timestamp BIGINT NOT NULL,
    block_number BIGINT NOT NULL,
    total_supply NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address, token_id, block_timestamp, block_number)
);

CREATE INDEX af_merchant_moe_token_supply_hist_token_block_desc_index ON af_merchant_moe_token_supply_hist (position_token_address DESC, block_timestamp DESC);

CREATE TABLE IF NOT EXISTS af_holding_balance_merchantmoe_period (
    period_date DATE NOT NULL,
    protocol_id VARCHAR NOT NULL,
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC NOT NULL,
    wallet_address BYTEA NOT NULL,
    token0_address BYTEA NOT NULL,
    token0_symbol VARCHAR NOT NULL,
    token0_balance NUMERIC(100, 18),
    token1_address BYTEA NOT NULL,
    token1_symbol VARCHAR NOT NULL,
    token1_balance NUMERIC(100, 18),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (period_date, protocol_id, position_token_address, token_id, wallet_address)
);

CREATE INDEX af_holding_balance_merchantmoe_period_period_date ON af_holding_balance_merchantmoe_period (period_date);

CREATE TABLE IF NOT EXISTS af_holding_balance_uniswap_v3_period (
    period_date DATE NOT NULL,
    protocol_id VARCHAR NOT NULL,
    position_token_address BYTEA NOT NULL,
    token_id INTEGER NOT NULL,
    wallet_address BYTEA NOT NULL,
    token0_address BYTEA NOT NULL,
    token0_symbol VARCHAR NOT NULL,
    token0_balance NUMERIC(100, 18),
    token1_address BYTEA NOT NULL,
    token1_symbol VARCHAR NOT NULL,
    token1_balance NUMERIC(100, 18),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (period_date, protocol_id, position_token_address, token_id)
);

CREATE INDEX af_holding_balance_uniswap_v3_period_period_date ON af_holding_balance_uniswap_v3_period (period_date);

CREATE TABLE IF NOT EXISTS af_merchant_moe_token_bin_hist_period (
    period_date DATE NOT NULL,
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    reserve0_bin NUMERIC(100),
    reserve1_bin NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (period_date, position_token_address, token_id)
);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pool_prices_daily (
    block_date DATE NOT NULL,
    pool_address BYTEA NOT NULL,
    sqrt_price_x96 NUMERIC(78),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (block_date, pool_address)
);

CREATE INDEX af_uniswap_v3_pool_prices_daily_block_date_index ON af_uniswap_v3_pool_prices_daily (block_date);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pool_prices_period (
    period_date DATE NOT NULL,
    pool_address BYTEA NOT NULL,
    sqrt_price_x96 NUMERIC(78),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (period_date, pool_address)
);

CREATE INDEX af_uniswap_v3_pool_prices_period_period_date_index ON af_uniswap_v3_pool_prices_period (period_date);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_data_daily (
    block_date DATE NOT NULL,
    position_token_address BYTEA NOT NULL,
    token_id INTEGER NOT NULL,
    wallet_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    liquidity NUMERIC(78),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (block_date, position_token_address, token_id)
);

CREATE INDEX af_uniswap_v3_token_data_daily_index ON af_uniswap_v3_token_data_daily (block_date);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_data_period (
    period_date DATE NOT NULL,
    position_token_address BYTEA NOT NULL,
    token_id INTEGER NOT NULL,
    wallet_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    liquidity NUMERIC(78),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (period_date, position_token_address, token_id)
);

CREATE INDEX af_uniswap_v3_token_data_period_date_index ON af_uniswap_v3_token_data_period (period_date);

UPDATE alembic_version SET version_num='c609922eae7a' WHERE alembic_version.version_num = '3dd9b90d2e31';

COMMIT;