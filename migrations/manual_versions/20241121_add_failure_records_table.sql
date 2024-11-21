BEGIN;

-- Running upgrade 3bd2e3099bae -> f846e3abeb18

CREATE TABLE IF NOT EXISTS failures_records (
    record_id BIGSERIAL NOT NULL,
    mission_sign VARCHAR,
    output_types VARCHAR,
    start_block_number BIGINT,
    end_block_number BIGINT,
    exception_stage VARCHAR,
    exception JSON,
    crash_time TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (record_id)
);

UPDATE alembic_version SET version_num='f846e3abeb18' WHERE alembic_version.version_num = '3bd2e3099bae';

COMMIT;