BEGIN;

-- Running upgrade 43d14640a8ac -> f4efa18760cc

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pool_prices_current (
    pool_address BYTEA NOT NULL,
    block_number BIGINT,
    block_timestamp BIGINT,
    factory_address BYTEA,
    sqrt_price_x96 NUMERIC(100),
    tick NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (pool_address)
);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pool_prices_hist (
    pool_address BYTEA NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    sqrt_price_x96 NUMERIC(100),
    tick NUMERIC(100),
    factory_address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (pool_address, block_timestamp, block_number)
);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pool_swap_hist (
    pool_address BYTEA NOT NULL,
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    block_number BIGINT,
    block_timestamp BIGINT,
    position_token_address BYTEA,
    transaction_from_address BYTEA,
    sender BYTEA,
    recipient BYTEA,
    liquidity NUMERIC(100),
    tick NUMERIC(100),
    sqrt_price_x96 NUMERIC(100),
    amount0 NUMERIC(100),
    amount1 NUMERIC(100),
    token0_address BYTEA,
    token1_address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (pool_address, transaction_hash, log_index)
);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_pools (
    position_token_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    factory_address BYTEA,
    token0_address BYTEA,
    token1_address BYTEA,
    fee NUMERIC(100),
    tick_spacing NUMERIC(100),
    block_number BIGINT,
    block_timestamp BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, pool_address)
);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_collect_fee_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    log_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    owner BYTEA,
    recipient BYTEA,
    amount0 NUMERIC(100),
    amount1 NUMERIC(100),
    pool_address BYTEA,
    token0_address BYTEA,
    token1_address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address, token_id, block_timestamp, block_number, log_index)
);

CREATE INDEX af_uniswap_v3_token_collect_fee_hist_owner_index ON af_uniswap_v3_token_collect_fee_hist (owner);

CREATE INDEX af_uniswap_v3_token_collect_fee_hist_pool_index ON af_uniswap_v3_token_collect_fee_hist (pool_address);

CREATE INDEX af_uniswap_v3_token_collect_fee_hist_token0_index ON af_uniswap_v3_token_collect_fee_hist (token0_address);

CREATE INDEX af_uniswap_v3_token_collect_fee_hist_token1_index ON af_uniswap_v3_token_collect_fee_hist (token1_address);

CREATE INDEX af_uniswap_v3_token_collect_fee_hist_token_id_index ON af_uniswap_v3_token_collect_fee_hist (token_id);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_data_current (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_number BIGINT,
    block_timestamp BIGINT,
    wallet_address BYTEA,
    pool_address BYTEA,
    liquidity NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, token_id)
);

CREATE INDEX af_uniswap_v3_token_data_current_wallet_desc_index ON af_uniswap_v3_token_data_current (wallet_address DESC);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_data_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    wallet_address BYTEA,
    pool_address BYTEA,
    liquidity NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address, token_id, block_timestamp, block_number)
);

CREATE INDEX af_uniswap_v3_token_data_hist_token_block_desc_index ON af_uniswap_v3_token_data_hist (position_token_address DESC, block_timestamp DESC);

CREATE INDEX af_uniswap_v3_token_data_hist_wallet_token_block_desc_index ON af_uniswap_v3_token_data_hist (wallet_address DESC, position_token_address DESC, block_timestamp DESC);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_token_liquidity_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    log_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    owner BYTEA,
    liquidity NUMERIC(100),
    amount0 NUMERIC(100),
    amount1 NUMERIC(100),
    pool_address BYTEA,
    token0_address BYTEA,
    token1_address BYTEA,
    action_type VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (position_token_address, token_id, block_timestamp, block_number, log_index)
);

CREATE INDEX af_uniswap_v3_token_liquidity_hist_owner_index ON af_uniswap_v3_token_liquidity_hist (owner);

CREATE INDEX af_uniswap_v3_token_liquidity_hist_pool_index ON af_uniswap_v3_token_liquidity_hist (pool_address);

CREATE INDEX af_uniswap_v3_token_liquidity_hist_token0_index ON af_uniswap_v3_token_liquidity_hist (token0_address);

CREATE INDEX af_uniswap_v3_token_liquidity_hist_token1_index ON af_uniswap_v3_token_liquidity_hist (token1_address);

CREATE INDEX af_uniswap_v3_token_liquidity_hist_token_id_index ON af_uniswap_v3_token_liquidity_hist (token_id);

CREATE TABLE IF NOT EXISTS af_uniswap_v3_tokens (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    pool_address BYTEA,
    tick_lower NUMERIC(100),
    tick_upper NUMERIC(100),
    fee NUMERIC(100),
    block_number BIGINT,
    block_timestamp BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, token_id)
);

CREATE INDEX af_uniswap_v3_tokens_nft_index ON af_uniswap_v3_tokens (position_token_address);

DROP INDEX feature_uniswap_v3_tokens_nft_index;

DROP TABLE feature_uniswap_v3_tokens;

DROP TABLE feature_uniswap_v3_pools;

UPDATE alembic_version SET version_num='f4efa18760cc' WHERE alembic_version.version_num = '43d14640a8ac';

COMMIT;