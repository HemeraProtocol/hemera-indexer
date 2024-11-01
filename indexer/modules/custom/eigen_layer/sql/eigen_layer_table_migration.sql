BEGIN;

CREATE TABLE IF NOT EXISTS af_eigen_layer_address_current (
    address BYTEA NOT NULL,
    strategy BYTEA NOT NULL,
    token BYTEA,
    deposit_amount NUMERIC(100),
    start_withdraw_amount NUMERIC(100),
    finish_withdraw_amount NUMERIC(100),
    d_s NUMERIC(100),
    d_f NUMERIC(100),
    s_f NUMERIC(100),
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
    topic0 BYTEA,
    from_address BYTEA,
    to_address BYTEA,
    token BYTEA,
    amount NUMERIC(100),
    balance NUMERIC(100),
    staker BYTEA,
    operator BYTEA,
    withdrawer BYTEA,
    shares NUMERIC(100),
    withdrawroot BYTEA,
    strategy BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index, internal_idx)
);

COMMIT;