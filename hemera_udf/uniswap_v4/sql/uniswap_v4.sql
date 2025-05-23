CREATE TABLE af_uniswap_v4_pools (
    position_token_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    factory_address BYTEA,
    token0_address BYTEA,
    token1_address BYTEA,
    fee NUMERIC(100),
    tick_spacing NUMERIC(100),
    hook_address BYTEA,
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (position_token_address, pool_address)
);

CREATE TABLE af_uniswap_v4_hooks (
    hook_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    factory_address BYTEA,
    hook_type TEXT,  -- e.g., "fee", "dynamic_fee", "limit_order", etc.
    hook_data TEXT,  -- JSON string of hook-specific data
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (hook_address, pool_address)
);


-- Swaps table to track swap events
CREATE TABLE af_uniswap_v4_swaps (
    tx_hash BYTEA NOT NULL,
    log_index BIGINT NOT NULL,
    pool_address BYTEA NOT NULL,
    sender_address BYTEA NOT NULL,
    recipient_address BYTEA NOT NULL,
    token0_delta NUMERIC(100),
    token1_delta NUMERIC(100),
    sqrt_price_x96_before NUMERIC(100),
    sqrt_price_x96_after NUMERIC(100),
    liquidity_before NUMERIC(100),
    liquidity_after NUMERIC(100),
    tick_before BIGINT,
    tick_after BIGINT,
    hook_data TEXT,  -- JSON string of hook-specific data for the swap
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (tx_hash, log_index)
);

-- Liquidity changes table to track mint/burn events
CREATE TABLE af_uniswap_v4_liquidity_changes (
    tx_hash BYTEA NOT NULL,
    log_index BIGINT NOT NULL,
    pool_address BYTEA NOT NULL,
    position_id BYTEA,
    sender_address BYTEA NOT NULL,
    recipient_address BYTEA NOT NULL,
    lower_tick BIGINT,
    upper_tick BIGINT,
    delta_liquidity NUMERIC(100),
    token0_delta NUMERIC(100),
    token1_delta NUMERIC(100),
    event_type TEXT NOT NULL, -- 'mint' or 'burn'
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (tx_hash, log_index)
);



-- Pool current prices
CREATE TABLE af_uniswap_v4_pool_current_prices (
    pool_address BYTEA NOT NULL PRIMARY KEY,
    token0_address BYTEA NOT NULL,
    token1_address BYTEA NOT NULL,
    token0_price NUMERIC(100), -- Price of token0 in terms of token1
    token1_price NUMERIC(100), -- Price of token1 in terms of token0
    sqrt_price_x96 NUMERIC(100),
    tick BIGINT,
    liquidity NUMERIC(100),
    token0_price_usd NUMERIC(100),
    token1_price_usd NUMERIC(100),
    last_updated_block_number BIGINT,
    last_updated_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

-- Pool price history
CREATE TABLE af_uniswap_v4_pool_prices (
    pool_address BYTEA NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    token0_address BYTEA NOT NULL,
    token1_address BYTEA NOT NULL,
    token0_price NUMERIC(100), -- Price of token0 in terms of token1
    token1_price NUMERIC(100), -- Price of token1 in terms of token0
    sqrt_price_x96 NUMERIC(100),
    tick BIGINT,
    liquidity NUMERIC(100),
    token0_price_usd NUMERIC(100),
    token1_price_usd NUMERIC(100),
    block_number BIGINT,
    create_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (pool_address, timestamp)
);


CREATE TABLE af_uniswap_v4_swap_hist(
    pool_address BYTEA NOT NULL,
    transaction_hash BYTEA NOT NULL,
    log_index BIGINT NOT NULL,
    position_token_address BYTEA,
    transaction_from_address BYTEA,
    sender BYTEA,
    recipient BYTEA,
    amount0 NUMERIC(100),
    amount1 NUMERIC(100),
    token0_price NUMERIC(100),
    token1_price NUMERIC(100),
    amount_usd NUMERIC(100),
    liquidity NUMERIC(100),
    tick NUMERIC(100),
    sqrt_price_x96 NUMERIC(100),
    token0_address BYTEA,
    token1_address BYTEA,
    hook_data TEXT,  -- JSON string of hook-related data
    block_number BIGINT,
    block_timestamp TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pool_address, transaction_hash, log_index)
);

CREATE INDEX idx_af_uniswap_v4_pools_pool_address ON af_uniswap_v4_pools(pool_address);
CREATE INDEX idx_af_uniswap_v4_pools_factory_address ON af_uniswap_v4_pools(factory_address);
CREATE INDEX idx_af_uniswap_v4_pools_token0_address ON af_uniswap_v4_pools(token0_address);
CREATE INDEX idx_af_uniswap_v4_pools_token1_address ON af_uniswap_v4_pools(token1_address);

CREATE INDEX idx_af_uniswap_v4_hooks_hook_address ON af_uniswap_v4_hooks(hook_address);
CREATE INDEX idx_af_uniswap_v4_hooks_factory_address ON af_uniswap_v4_hooks(factory_address);

-- New indices for additional tables

CREATE INDEX idx_af_uniswap_v4_swaps_pool_address ON af_uniswap_v4_swaps(pool_address);
CREATE INDEX idx_af_uniswap_v4_swaps_block_timestamp ON af_uniswap_v4_swaps(block_timestamp);


-- Indices for pool price tables
CREATE INDEX idx_af_uniswap_v4_pool_prices_timestamp ON af_uniswap_v4_pool_prices(timestamp);
CREATE INDEX idx_af_uniswap_v4_pool_prices_token0_address ON af_uniswap_v4_pool_prices(token0_address);
CREATE INDEX idx_af_uniswap_v4_pool_prices_token1_address ON af_uniswap_v4_pool_prices(token1_address);

-- Indices for ETH swap history
CREATE INDEX idx_af_uniswap_v4_swap_hist_pool_address ON af_uniswap_v4_swap_hist(pool_address);
CREATE INDEX idx_af_uniswap_v4_swap_hist_token_address ON af_uniswap_v4_swap_hist(token_address);
CREATE INDEX idx_af_uniswap_v4_swap_hist_block_timestamp ON af_uniswap_v4_swap_hist(block_timestamp);
