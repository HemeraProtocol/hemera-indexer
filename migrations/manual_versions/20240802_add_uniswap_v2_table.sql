BEGIN;

-- Running upgrade e3a3e2114b9c -> aa99dd347ef1

CREATE TABLE feature_uniswap_v2_pools (
    factory_address BYTEA NOT NULL,
    pool_address BYTEA NOT NULL,
    token0_address BYTEA,
    token1_address BYTEA,
    length NUMERIC(100),
    called_block_number BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (factory_address, pool_address)
);

ALTER TABLE feature_uniswap_v3_pools ADD COLUMN called_block_number BIGINT;

ALTER TABLE feature_uniswap_v3_pools DROP COLUMN mint_block_number;

ALTER TABLE feature_uniswap_v3_tokens ADD COLUMN called_block_number BIGINT;

ALTER TABLE feature_uniswap_v3_tokens DROP COLUMN mint_block_number;

UPDATE alembic_version SET version_num='aa99dd347ef1' WHERE alembic_version.version_num = 'e3a3e2114b9c';

COMMIT;