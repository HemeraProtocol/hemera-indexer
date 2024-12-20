BEGIN;

CREATE TABLE IF NOT EXISTS af_eigen_layer_address_current (
    address BYTEA NOT NULL,
    strategy BYTEA NOT NULL,
    token BYTEA,
    deposit_amount NUMERIC(100),
    start_withdraw_amount NUMERIC(100),
    finish_withdraw_amount NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, strategy)
);

CREATE TABLE IF NOT EXISTS af_eigen_layer_records (
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    internal_idx INTEGER NOT NULL,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    method VARCHAR,
    event_name VARCHAR,
    strategy BYTEA,
    token BYTEA,
    staker BYTEA,
    shares NUMERIC(100),
    withdrawer BYTEA,
    withdrawroot BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index, internal_idx)
);

COMMIT;