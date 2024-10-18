BEGIN;

-- Running upgrade 9a1e927f02bb -> 040e5251f45d

CREATE TABLE exception_records (
    id BIGSERIAL NOT NULL,
    block_number BIGINT,
    dataclass VARCHAR,
    level VARCHAR,
    message_type VARCHAR,
    message VARCHAR,
    exception_env JSONB,
    record_time TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

UPDATE alembic_version SET version_num='040e5251f45d' WHERE alembic_version.version_num = '9a1e927f02bb';

COMMIT;