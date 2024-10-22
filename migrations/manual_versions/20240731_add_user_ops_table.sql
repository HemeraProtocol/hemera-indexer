BEGIN;

-- Running upgrade 3d5ce8939570 -> 9a1e927f02bb

CREATE TABLE user_operations_results (
    user_op_hash BYTEA NOT NULL,
    sender VARCHAR(42),
    paymaster VARCHAR(42),
    nonce NUMERIC,
    status BOOLEAN,
    actual_gas_cost NUMERIC,
    actual_gas_used NUMERIC,
    init_code BYTEA,
    call_data BYTEA,
    call_gas_limit NUMERIC,
    verification_gas_limit NUMERIC,
    pre_verification_gas NUMERIC,
    max_fee_per_gas NUMERIC,
    max_priority_fee_per_gas NUMERIC,
    paymaster_and_data BYTEA,
    signature BYTEA,
    transactions_hash BYTEA,
    transactions_index INTEGER,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    bundler VARCHAR(42),
    start_log_index INTEGER,
    end_log_index INTEGER,
    PRIMARY KEY (user_op_hash)
);

CREATE INDEX transactions_hash_index ON user_operations_results (transactions_hash);

UPDATE alembic_version SET version_num='9a1e927f02bb' WHERE alembic_version.version_num = '3d5ce8939570';

COMMIT;