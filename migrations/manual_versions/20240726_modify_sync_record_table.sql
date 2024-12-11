BEGIN;

-- Running upgrade 9f2cf385645f -> 0b922153e040

DROP TABLE sync_record;

CREATE TABLE IF NOT EXISTS sync_record (
    mission_sign VARCHAR NOT NULL,
    last_block_number BIGINT,
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (mission_sign)
);

UPDATE alembic_version SET version_num='0b922153e040' WHERE alembic_version.version_num = '9f2cf385645f';

COMMIT;