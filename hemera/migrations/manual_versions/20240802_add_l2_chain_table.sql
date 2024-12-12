BEGIN;

-- Running upgrade 040e5251f45d -> e3a3e2114b9c

CREATE TABLE IF NOT EXISTS arbitrum_state_batches (
    node_num SERIAL NOT NULL,
    create_l1_block_number INTEGER,
    create_l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_l1_block_hash VARCHAR,
    create_l1_transaction_hash VARCHAR,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash VARCHAR,
    l1_transaction_hash VARCHAR,
    parent_node_hash VARCHAR,
    node_hash VARCHAR,
    block_hash VARCHAR,
    send_root VARCHAR,
    start_block_number INTEGER,
    end_block_number INTEGER,
    transaction_count INTEGER,
    block_count INTEGER,
    PRIMARY KEY (node_num)
);

CREATE TABLE IF NOT EXISTS arbitrum_transaction_batches (
    batch_index SERIAL NOT NULL,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash VARCHAR,
    l1_transaction_hash VARCHAR,
    batch_root VARCHAR,
    start_block_number INTEGER,
    end_block_number INTEGER,
    transaction_count INTEGER,
    block_count INTEGER,
    PRIMARY KEY (batch_index)
);

CREATE TABLE IF NOT EXISTS bridge_tokens (
    l1_token_address BYTEA NOT NULL,
    l2_token_address BYTEA NOT NULL,
    PRIMARY KEY (l1_token_address, l2_token_address)
);

CREATE TABLE IF NOT EXISTS data_store_tx_mapping (
    data_store_id INTEGER NOT NULL,
    index INTEGER NOT NULL,
    block_number INTEGER,
    transaction_hash VARCHAR,
    PRIMARY KEY (data_store_id, index)
);

CREATE TABLE IF NOT EXISTS data_stores (
    id SERIAL NOT NULL,
    store_number INTEGER,
    duration_data_store_id INTEGER,
    index INTEGER,
    data_commitment VARCHAR,
    msg_hash VARCHAR,
    init_time TIMESTAMP WITHOUT TIME ZONE,
    expire_time TIMESTAMP WITHOUT TIME ZONE,
    duration INTEGER,
    store_period_length INTEGER,
    fee INTEGER,
    confirmer VARCHAR,
    header VARCHAR,
    init_tx_hash VARCHAR,
    init_gas_used INTEGER,
    init_block_number INTEGER,
    confirmed BOOLEAN,
    signatory_record VARCHAR,
    confirm_tx_hash VARCHAR,
    confirm_gas_used INTEGER,
    batch_index INTEGER,
    tx_count INTEGER,
    block_count INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS l1_state_batches (
    batch_index SERIAL NOT NULL,
    previous_total_elements INTEGER,
    batch_size INTEGER,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash VARCHAR,
    l1_transaction_hash VARCHAR,
    extra_data VARCHAR,
    batch_root VARCHAR,
    PRIMARY KEY (batch_index)
);

CREATE TABLE IF NOT EXISTS l1_to_l2_bridge_transactions (
    msg_hash BYTEA NOT NULL,
    version INTEGER,
    index INTEGER,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash BYTEA,
    l1_transaction_hash BYTEA,
    l1_from_address BYTEA,
    l1_to_address BYTEA,
    l2_block_number INTEGER,
    l2_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l2_block_hash BYTEA,
    l2_transaction_hash BYTEA,
    l2_from_address BYTEA,
    l2_to_address BYTEA,
    amount NUMERIC(78),
    from_address BYTEA,
    to_address BYTEA,
    l1_token_address BYTEA,
    l2_token_address BYTEA,
    extra_info JSON,
    _type INTEGER,
    sender BYTEA,
    target BYTEA,
    data BYTEA,
    PRIMARY KEY (msg_hash)
);

CREATE TABLE IF NOT EXISTS l2_to_l1_bridge_transactions (
    msg_hash BYTEA NOT NULL,
    version INTEGER,
    index INTEGER,
    l2_block_number INTEGER,
    l2_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l2_block_hash BYTEA,
    l2_transaction_hash BYTEA,
    l2_from_address BYTEA,
    l2_to_address BYTEA,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash BYTEA,
    l1_transaction_hash BYTEA,
    l1_from_address BYTEA,
    l1_to_address BYTEA,
    amount NUMERIC(78),
    from_address BYTEA,
    to_address BYTEA,
    l1_token_address BYTEA,
    l2_token_address BYTEA,
    extra_info JSON,
    _type INTEGER,
    l1_proven_transaction_hash BYTEA,
    l1_proven_block_number INTEGER,
    l1_proven_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_proven_block_hash BYTEA,
    l1_proven_from_address BYTEA,
    l1_proven_to_address BYTEA,
    PRIMARY KEY (msg_hash)
);

CREATE TABLE IF NOT EXISTS linea_batches (
    number SERIAL NOT NULL,
    verify_tx_hash VARCHAR,
    verify_block_number INTEGER,
    timestamp TIMESTAMP WITHOUT TIME ZONE,
    blocks INTEGER[],
    transactions VARCHAR[],
    last_finalized_block_number INTEGER,
    tx_count INTEGER,
    block_count INTEGER,
    PRIMARY KEY (number)
);

CREATE TABLE IF NOT EXISTS mantle_batches (
    index SERIAL NOT NULL,
    data_store_index INTEGER,
    upgrade_data_store_id INTEGER,
    data_store_id INTEGER,
    status INTEGER,
    confirm_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (index)
);

CREATE TABLE IF NOT EXISTS op_bedrock_state_batches (
    batch_index SERIAL NOT NULL,
    l1_block_number INTEGER,
    l1_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    l1_block_hash VARCHAR,
    l1_transaction_hash VARCHAR,
    start_block_number INTEGER,
    end_block_number INTEGER,
    batch_root VARCHAR,
    transaction_count INTEGER,
    block_count INTEGER,
    PRIMARY KEY (batch_index)
);

CREATE TABLE IF NOT EXISTS op_da_transactions (
    receipt_blob_gas_used INTEGER,
    receipt_blob_gas_price NUMERIC,
    blob_versioned_hashes VARCHAR[],
    hash VARCHAR NOT NULL,
    nonce INTEGER,
    transaction_index INTEGER,
    from_address VARCHAR,
    to_address VARCHAR,
    value NUMERIC,
    gas INTEGER,
    gas_price INTEGER,
    input VARCHAR,
    receipt_cumulative_gas_used INTEGER,
    receipt_gas_used INTEGER,
    receipt_contract_address VARCHAR,
    receipt_root VARCHAR,
    receipt_status INTEGER,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    block_number INTEGER,
    block_hash VARCHAR,
    max_fee_per_gas INTEGER,
    max_priority_fee_per_gas INTEGER,
    transaction_type INTEGER,
    receipt_effective_gas_price INTEGER,
    PRIMARY KEY (hash)
);

CREATE TABLE IF NOT EXISTS zkevm_batches (
    batch_index SERIAL NOT NULL,
    coinbase VARCHAR,
    state_root VARCHAR,
    global_exit_root VARCHAR,
    mainnet_exit_root VARCHAR,
    rollup_exit_root VARCHAR,
    local_exit_root VARCHAR,
    acc_input_hash VARCHAR,
    timestamp TIMESTAMP WITHOUT TIME ZONE,
    transactions VARCHAR[],
    blocks INTEGER[],
    start_block_number INTEGER,
    end_block_number INTEGER,
    block_count INTEGER,
    transaction_count INTEGER,
    sequence_batch_tx_hash VARCHAR,
    sequence_batch_block_number INTEGER,
    sequence_batch_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    verify_batch_tx_hash VARCHAR,
    verify_batch_block_number INTEGER,
    verify_batch_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    number INTEGER,
    send_sequences_tx_hash VARCHAR,
    PRIMARY KEY (batch_index)
);

UPDATE alembic_version SET version_num='e3a3e2114b9c' WHERE alembic_version.version_num = '040e5251f45d';

COMMIT;