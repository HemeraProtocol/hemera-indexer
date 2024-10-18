BEGIN;

-- Running upgrade c609922eae7a -> 67015d9fa59b

CREATE TABLE af_merchant_moe_pool_data_current (
    pool_address BYTEA NOT NULL,
    block_timestamp BIGINT,
    block_number BIGINT,
    active_id BIGINT,
    bin_step BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN,
    PRIMARY KEY (pool_address)
);

CREATE TABLE af_merchant_moe_pool_data_hist (
    pool_address BYTEA NOT NULL,
    block_timestamp BIGINT NOT NULL,
    block_number BIGINT NOT NULL,
    active_id BIGINT,
    bin_step BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN,
    PRIMARY KEY (pool_address, block_timestamp, block_number)
);

CREATE TABLE af_staked_fbtc_current (
    vault_address BYTEA NOT NULL,
    wallet_address BYTEA NOT NULL,
    block_number BIGINT,
    block_timestamp BIGINT,
    amount NUMERIC(100),
    changed_amount NUMERIC(100),
    protocol_id VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (vault_address, wallet_address)
);

CREATE INDEX af_staked_fbtc_current_protocol_block_desc_index ON af_staked_fbtc_current (protocol_id DESC);

CREATE INDEX af_staked_fbtc_current_wallet_block_desc_index ON af_staked_fbtc_current (wallet_address DESC);

CREATE TABLE af_staked_fbtc_detail_hist (
    vault_address BYTEA NOT NULL,
    wallet_address BYTEA NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    amount NUMERIC(100),
    changed_amount NUMERIC(100),
    protocol_id VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN,
    PRIMARY KEY (vault_address, wallet_address, block_timestamp, block_number)
);

CREATE INDEX af_staked_fbtc_detail_hist_protocol_block_desc_index ON af_staked_fbtc_detail_hist (protocol_id DESC, block_timestamp DESC);

CREATE INDEX af_staked_fbtc_detail_hist_wallet_block_desc_index ON af_staked_fbtc_detail_hist (wallet_address DESC, block_timestamp DESC);

UPDATE alembic_version SET version_num='67015d9fa59b' WHERE alembic_version.version_num = 'c609922eae7a';

COMMIT;