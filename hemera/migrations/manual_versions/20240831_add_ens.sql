BEGIN;

-- Running upgrade 6c2eecd6316b -> 43d14640a8ac

CREATE TABLE IF NOT EXISTS af_ens_address_current (
    address BYTEA NOT NULL,
    name VARCHAR,
    reverse_node BYTEA,
    block_number BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS af_ens_event (
    transaction_hash BYTEA NOT NULL,
    transaction_index INTEGER NOT NULL,
    log_index INTEGER NOT NULL,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    method VARCHAR,
    event_name VARCHAR,
    topic0 VARCHAR,
    from_address BYTEA,
    to_address BYTEA,
    base_node BYTEA,
    node BYTEA,
    label BYTEA,
    name VARCHAR,
    expires TIMESTAMP WITHOUT TIME ZONE,
    owner BYTEA,
    resolver BYTEA,
    registrant BYTEA,
    address BYTEA,
    reverse_base_node BYTEA,
    reverse_node BYTEA,
    reverse_label BYTEA,
    reverse_name VARCHAR,
    token_id NUMERIC(100),
    w_token_id NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    CONSTRAINT ens_tnx_log_index PRIMARY KEY (transaction_hash, log_index)
);

CREATE INDEX ens_event_address ON af_ens_event (from_address);

CREATE INDEX ens_idx_block_number_log_index ON af_ens_event (block_number, log_index DESC);

CREATE TABLE IF NOT EXISTS af_ens_node_current (
    node BYTEA NOT NULL,
    token_id NUMERIC(100),
    w_token_id NUMERIC(100),
    first_owned_by BYTEA,
    name VARCHAR,
    registration TIMESTAMP WITHOUT TIME ZONE,
    expires TIMESTAMP WITHOUT TIME ZONE,
    address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (node)
);

CREATE INDEX ens_idx_address ON af_ens_node_current (address);

CREATE INDEX ens_idx_name_md5 ON af_ens_node_current (md5(name));

UPDATE alembic_version SET version_num='43d14640a8ac' WHERE alembic_version.version_num = '6c2eecd6316b';

COMMIT;