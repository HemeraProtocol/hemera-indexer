BEGIN;

-- Running upgrade 0b922153e040 -> 3d5ce8939570

CREATE TABLE all_feature_value_records (
    feature_id NUMERIC(100) NOT NULL,
    block_number BIGINT NOT NULL,
    address BYTEA NOT NULL,
    value JSONB,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (block_number, feature_id, address)
);

CREATE INDEX all_feature_value_records_feature_block_index ON all_feature_value_records (feature_id, block_number DESC);

CREATE TABLE feature_uniswap_v3_pools (
    nft_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    token0_address BYTEA,
    token1_address BYTEA,
    fee NUMERIC(100),
    tick_spacing NUMERIC(100),
    mint_block_number BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (nft_address, pool_address)
);

CREATE TABLE feature_uniswap_v3_tokens (
    nft_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    pool_address BYTEA,
    tick_lower NUMERIC(100),
    tick_upper NUMERIC(100),
    fee NUMERIC(100),
    mint_block_number BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (nft_address, token_id)
);

CREATE INDEX feature_uniswap_v3_tokens_nft_index ON feature_uniswap_v3_tokens (nft_address);

UPDATE alembic_version SET version_num='3d5ce8939570' WHERE alembic_version.version_num = '0b922153e040';

COMMIT;