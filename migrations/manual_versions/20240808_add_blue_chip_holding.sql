BEGIN;

-- Running upgrade b86e241b5e18 -> 1b1c6a8b6c7b

CREATE TABLE IF NOT EXISTS feature_blue_chip_holders (
    wallet_address BYTEA NOT NULL,
    hold_detail JSONB,
    current_count BIGINT,
    called_block_number BIGINT,
    called_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (wallet_address)
);

UPDATE alembic_version SET version_num='1b1c6a8b6c7b' WHERE alembic_version.version_num = 'b86e241b5e18';

COMMIT;