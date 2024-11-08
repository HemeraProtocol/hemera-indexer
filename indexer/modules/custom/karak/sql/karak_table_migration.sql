BEGIN;

CREATE TABLE IF NOT EXISTS af_karak_address_current (
    address BYTEA NOT NULL,
    vault BYTEA NOT NULL,
    deposit_amount NUMERIC(100),
    start_withdraw_amount NUMERIC(100),
    finish_withdraw_amount NUMERIC(100),
    d_s NUMERIC(100),
    d_f NUMERIC(100),
    s_f NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, vault)
);

CREATE TABLE IF NOT EXISTS af_karak_records (
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    method VARCHAR,
    event_name VARCHAR,
    topic0 VARCHAR,
    from_address BYTEA,
    to_address BYTEA,
    token VARCHAR,
    vault BYTEA,
    amount NUMERIC(100),
    balance NUMERIC(100),
    staker VARCHAR,
    operator VARCHAR,
    withdrawer VARCHAR,
    shares NUMERIC(100),
    withdrawroot VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index)
);

CREATE TABLE IF NOT EXISTS af_karak_vault_token (
    vault BYTEA NOT NULL,
    token BYTEA NOT NULL,
    name VARCHAR,
    symbol VARCHAR,
    asset_type INTEGER,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (vault, token)
);

COMMIT;