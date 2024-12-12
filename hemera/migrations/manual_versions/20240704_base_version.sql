BEGIN;

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 5e4608933f64

CREATE TABLE IF NOT EXISTS address_coin_balances (
    address BYTEA NOT NULL,
    balance NUMERIC(100),
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, block_number)
);

CREATE TABLE IF NOT EXISTS address_token_balances (
    address BYTEA NOT NULL,
    token_id NUMERIC(78),
    token_type VARCHAR,
    token_address BYTEA NOT NULL,
    balance NUMERIC(100),
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, token_address, token_id, block_number)
);

CREATE TABLE IF NOT EXISTS block_ts_mapper (
    ts BIGSERIAL NOT NULL,
    block_number BIGINT,
    timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (ts)
);

CREATE INDEX block_ts_mapper_idx ON block_ts_mapper (block_number DESC);

CREATE TABLE IF NOT EXISTS blocks (
    hash BYTEA NOT NULL,
    number BIGINT,
    timestamp TIMESTAMP WITHOUT TIME ZONE,
    parent_hash BYTEA,
    nonce BYTEA,
    gas_limit NUMERIC(100),
    gas_used NUMERIC(100),
    base_fee_per_gas NUMERIC(100),
    difficulty NUMERIC(38),
    total_difficulty NUMERIC(38),
    size BIGINT,
    miner BYTEA,
    sha3_uncles BYTEA,
    transactions_root BYTEA,
    transactions_count BIGINT,
    state_root BYTEA,
    receipts_root BYTEA,
    extra_data BYTEA,
    withdrawals_root BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (hash)
);

CREATE INDEX blocks_number_index ON blocks (number DESC);

CREATE INDEX blocks_timestamp_index ON blocks (timestamp DESC);

CREATE TABLE IF NOT EXISTS contract_internal_transactions (
    trace_id VARCHAR NOT NULL,
    from_address BYTEA,
    to_address BYTEA,
    value NUMERIC(100),
    trace_type VARCHAR,
    call_type VARCHAR,
    gas NUMERIC(100),
    gas_used NUMERIC(100),
    trace_address INTEGER[],
    error TEXT,
    status INTEGER,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    transaction_index INTEGER,
    transaction_hash BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (trace_id)
);

CREATE INDEX contract_internal_transactions_transaction_hash_idx ON contract_internal_transactions (transaction_hash);

CREATE INDEX internal_transactions_address_number_transaction_index ON contract_internal_transactions (from_address, to_address, block_number DESC, transaction_index DESC);

CREATE INDEX internal_transactions_block_timestamp_index ON contract_internal_transactions (block_timestamp DESC);

CREATE TABLE IF NOT EXISTS contracts (
    address BYTEA NOT NULL,
    name VARCHAR,
    contract_creator BYTEA,
    creation_code BYTEA,
    deployed_code BYTEA,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    transaction_index INTEGER,
    transaction_hash BYTEA,
    official_website VARCHAR,
    description VARCHAR,
    email VARCHAR,
    social_list JSONB,
    is_verified BOOLEAN,
    is_proxy BOOLEAN,
    implementation_contract BYTEA,
    verified_implementation_contract BYTEA,
    proxy_standard VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS erc1155_token_holders (
    token_address BYTEA NOT NULL,
    wallet_address BYTEA NOT NULL,
    token_id NUMERIC(78) NOT NULL,
    balance_of NUMERIC(100),
    latest_call_contract_time TIMESTAMP WITHOUT TIME ZONE,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (token_address, wallet_address, token_id)
);

CREATE INDEX erc1155_token_holders_token_address_balance_of_index ON erc1155_token_holders (token_address, balance_of DESC);

CREATE TABLE IF NOT EXISTS erc1155_token_id_details (
    address BYTEA NOT NULL,
    token_id NUMERIC(78) NOT NULL,
    token_supply NUMERIC(78),
    token_uri VARCHAR,
    token_uri_info JSONB,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, token_id)
);

CREATE INDEX erc1155_detail_desc_address_id_index ON erc1155_token_id_details (address DESC, token_id);

CREATE TABLE IF NOT EXISTS erc1155_token_transfers (
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    from_address BYTEA,
    to_address BYTEA,
    token_address BYTEA,
    token_id NUMERIC(78),
    value NUMERIC(100),
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index)
);

CREATE INDEX erc1155_token_transfers_address_block_number_log_index_index ON erc1155_token_transfers (token_address, from_address, to_address, block_number DESC, log_index DESC);

CREATE INDEX erc1155_token_transfers_block_timestamp_index ON erc1155_token_transfers (block_timestamp DESC);

CREATE TABLE IF NOT EXISTS erc20_token_holders (
    token_address BYTEA NOT NULL,
    wallet_address BYTEA NOT NULL,
    balance_of NUMERIC(100),
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (token_address, wallet_address)
);

CREATE INDEX erc20_token_holders_token_address_balance_of_index ON erc20_token_holders (token_address, balance_of DESC);

CREATE TABLE IF NOT EXISTS erc20_token_transfers (
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    from_address BYTEA,
    to_address BYTEA,
    token_address BYTEA,
    value NUMERIC(100),
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index)
);

CREATE INDEX erc20_token_transfers_address_block_number_log_index_index ON erc20_token_transfers (token_address, from_address, to_address, block_number DESC, log_index DESC);

CREATE INDEX erc20_token_transfers_block_timestamp_index ON erc20_token_transfers (block_timestamp DESC);

CREATE TABLE IF NOT EXISTS erc721_token_holders (
    token_address BYTEA NOT NULL,
    wallet_address BYTEA NOT NULL,
    balance_of NUMERIC(100),
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (token_address, wallet_address)
);

CREATE INDEX erc721_token_holders_token_address_balance_of_index ON erc721_token_holders (token_address, balance_of DESC);

CREATE TABLE IF NOT EXISTS erc721_token_id_changes (
    address BYTEA NOT NULL,
    token_id NUMERIC(78) NOT NULL,
    token_owner BYTEA,
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, token_id, block_number)
);

CREATE INDEX erc721_change_address_id_number_desc_index ON erc721_token_id_changes (address, token_id, block_number DESC);

CREATE TABLE IF NOT EXISTS erc721_token_id_details (
    address BYTEA NOT NULL,
    token_id NUMERIC(78) NOT NULL,
    token_owner BYTEA,
    token_uri VARCHAR,
    token_uri_info JSONB,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, token_id)
);

CREATE INDEX erc721_detail_owner_address_id_index ON erc721_token_id_details (token_owner DESC, address, token_id);

CREATE TABLE IF NOT EXISTS erc721_token_transfers (
    transaction_hash BYTEA NOT NULL,
    log_index INTEGER NOT NULL,
    from_address BYTEA,
    to_address BYTEA,
    token_address BYTEA,
    token_id NUMERIC(78),
    token_uri JSONB,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash, log_index)
);

CREATE INDEX erc721_token_transfers_address_block_number_log_index_index ON erc721_token_transfers (token_address, from_address, to_address, block_number DESC, log_index DESC);

CREATE INDEX erc721_token_transfers_block_timestamp_index ON erc721_token_transfers (block_timestamp DESC);

CREATE TABLE IF NOT EXISTS fix_record (
    job_id SERIAL NOT NULL,
    start_block_number BIGINT,
    last_fixed_block_number BIGINT,
    remain_process INTEGER,
    job_status VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (job_id)
);

CREATE TABLE IF NOT EXISTS logs (
    log_index INTEGER NOT NULL,
    address BYTEA,
    data BYTEA,
    topic0 BYTEA,
    topic1 BYTEA,
    topic2 BYTEA,
    topic3 BYTEA,
    transaction_hash BYTEA NOT NULL,
    transaction_index INTEGER,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (log_index, transaction_hash)
);

CREATE INDEX logs_address_block_number_log_index_index ON logs (address, block_number DESC, log_index DESC);

CREATE INDEX logs_block_timestamp_index ON logs (block_timestamp DESC);

CREATE TABLE IF NOT EXISTS sync_record (
    mission_type VARCHAR NOT NULL,
    entity_types INTEGER NOT NULL,
    last_block_number BIGINT,
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (mission_type, entity_types)
);

CREATE TABLE IF NOT EXISTS tokens (
    address BYTEA NOT NULL,
    name VARCHAR,
    symbol VARCHAR,
    total_supply NUMERIC(100),
    decimals NUMERIC(100),
    token_type VARCHAR,
    holder_count INTEGER,
    transfer_count INTEGER,
    icon_url VARCHAR,
    urls JSONB,
    volume_24h NUMERIC(38, 2),
    price NUMERIC(38, 6),
    previous_price NUMERIC(38, 6),
    market_cap NUMERIC(38, 2),
    on_chain_market_cap NUMERIC(38, 2),
    is_verified BOOLEAN,
    cmc_id INTEGER,
    cmc_slug VARCHAR,
    gecko_id VARCHAR,
    description VARCHAR,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address)
);

CREATE INDEX tokens_symbol_index ON tokens (symbol);

CREATE INDEX tokens_type_index ON tokens (token_type);

CREATE TABLE IF NOT EXISTS traces (
    trace_id VARCHAR NOT NULL,
    from_address BYTEA,
    to_address BYTEA,
    value NUMERIC(100),
    input BYTEA,
    output BYTEA,
    trace_type VARCHAR,
    call_type VARCHAR,
    gas NUMERIC(100),
    gas_used NUMERIC(100),
    subtraces INTEGER,
    trace_address INTEGER[],
    error TEXT,
    status INTEGER,
    block_number BIGINT,
    block_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    transaction_index INTEGER,
    transaction_hash BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (trace_id)
);

CREATE INDEX traces_address_block_timestamp_index ON traces (from_address, to_address, block_timestamp DESC);

CREATE INDEX traces_transaction_hash_index ON traces (transaction_hash);

CREATE TABLE IF NOT EXISTS transactions (
    hash BYTEA NOT NULL,
    transaction_index INTEGER,
    from_address BYTEA,
    to_address BYTEA,
    value NUMERIC(100),
    transaction_type INTEGER,
    input BYTEA,
    nonce INTEGER,
    block_hash BYTEA,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    gas NUMERIC(100),
    gas_price NUMERIC(100),
    max_fee_per_gas NUMERIC(100),
    max_priority_fee_per_gas NUMERIC(100),
    receipt_root BYTEA,
    receipt_status INTEGER,
    receipt_gas_used NUMERIC(100),
    receipt_cumulative_gas_used NUMERIC(100),
    receipt_effective_gas_price NUMERIC(100),
    receipt_l1_fee NUMERIC(100),
    receipt_l1_fee_scalar NUMERIC(100, 18),
    receipt_l1_gas_used NUMERIC(100),
    receipt_l1_gas_price NUMERIC(100),
    receipt_blob_gas_used NUMERIC(100),
    receipt_blob_gas_price NUMERIC(100),
    blob_versioned_hashes BYTEA[],
    receipt_contract_address BYTEA,
    exist_error BOOLEAN,
    error TEXT,
    revert_reason TEXT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (hash)
);

CREATE INDEX transactions_address_block_number_transaction_idx ON transactions (from_address, to_address, block_number DESC, transaction_index DESC);

CREATE INDEX transactions_block_timestamp_block_number_index ON transactions (block_timestamp DESC, block_number DESC);

INSERT INTO alembic_version (version_num) VALUES ('5e4608933f64') RETURNING alembic_version.version_num;

COMMIT;