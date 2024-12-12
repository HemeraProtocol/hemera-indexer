BEGIN;

-- Running upgrade bc23aa19668e -> 3bd2e3099bae

CREATE TABLE IF NOT EXISTS address_contract_operations (
    address BYTEA NOT NULL,
    trace_from_address BYTEA,
    contract_address BYTEA,
    trace_id TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    transaction_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    block_hash BYTEA,
    error TEXT,
    status INTEGER,
    creation_code BYTEA,
    deployed_code BYTEA,
    gas NUMERIC(100),
    gas_used NUMERIC(100),
    trace_type TEXT,
    call_type TEXT,
    transaction_receipt_status INTEGER,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, trace_id, block_number, transaction_index, block_timestamp)
);

CREATE INDEX IF NOT EXISTS address_contract_operations_address_block_tn_t_idx ON address_contract_operations (address, block_timestamp DESC, block_number DESC, transaction_index DESC);

CREATE TABLE IF NOT EXISTS address_internal_transactions (
    address BYTEA NOT NULL,
    trace_id TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    transaction_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    block_hash BYTEA,
    error TEXT,
    status INTEGER,
    input_method TEXT,
    value NUMERIC(100),
    gas NUMERIC(100),
    gas_used NUMERIC(100),
    trace_type TEXT,
    call_type TEXT,
    txn_type SMALLINT,
    related_address BYTEA,
    transaction_receipt_status INTEGER,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, trace_id, block_number, transaction_index, block_timestamp)
);

CREATE INDEX address_internal_transactions_address_nt_t_idx ON address_internal_transactions (address, block_timestamp DESC, block_number DESC, transaction_index DESC);

CREATE TABLE IF NOT EXISTS af_erc1155_token_holdings_current (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    wallet_address BYTEA NOT NULL,
    block_number BIGINT,
    block_timestamp BIGINT,
    balance NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (position_token_address, token_id, wallet_address)
);

CREATE INDEX af_erc1155_token_holdings_current_token_block_desc_index ON af_erc1155_token_holdings_current (position_token_address DESC, block_timestamp DESC);

CREATE INDEX af_erc1155_token_holdings_current_wallet_block_desc_index ON af_erc1155_token_holdings_current (wallet_address DESC, block_timestamp DESC);

CREATE TABLE IF NOT EXISTS af_erc1155_token_holdings_hist (
    position_token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    wallet_address BYTEA NOT NULL,
    balance NUMERIC(100),
    block_number BIGINT NOT NULL,
    block_timestamp BIGINT NOT NULL,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN,
    PRIMARY KEY (position_token_address, token_id, wallet_address, block_timestamp, block_number)
);

CREATE INDEX feature_erc1155_token_holding_token_block_desc_index ON af_erc1155_token_holdings_hist (position_token_address DESC, block_timestamp DESC);

CREATE INDEX feature_erc1155_token_holding_token_wallet_block_desc_index ON af_erc1155_token_holdings_hist (position_token_address DESC, wallet_address DESC, block_number DESC);

CREATE TABLE IF NOT EXISTS af_index_daily_stats (
    address BYTEA NOT NULL,
    block_date DATE NOT NULL,
    transaction_in_count INTEGER,
    transaction_out_count INTEGER,
    transaction_self_count INTEGER,
    transaction_in_value BIGINT,
    transaction_out_value BIGINT,
    transaction_self_value BIGINT,
    transaction_in_fee NUMERIC,
    transaction_out_fee NUMERIC,
    transaction_self_fee NUMERIC,
    internal_transaction_in_count INTEGER,
    internal_transaction_out_count INTEGER,
    internal_transaction_self_count INTEGER,
    internal_transaction_in_value BIGINT,
    internal_transaction_out_value BIGINT,
    internal_transaction_self_value BIGINT,
    erc20_transfer_in_count INTEGER,
    erc20_transfer_out_count INTEGER,
    erc20_transfer_self_count INTEGER,
    nft_transfer_in_count INTEGER,
    nft_transfer_out_count INTEGER,
    nft_transfer_self_count INTEGER,
    nft_721_transfer_in_count INTEGER,
    nft_721_transfer_out_count INTEGER,
    nft_721_transfer_self_count INTEGER,
    nft_1155_transfer_in_count INTEGER,
    nft_1155_transfer_out_count INTEGER,
    nft_1155_transfer_self_count INTEGER,
    contract_creation_count INTEGER,
    contract_destruction_count INTEGER,
    contract_operation_count INTEGER,
    transaction_count INTEGER,
    internal_transaction_count INTEGER,
    erc20_transfer_count INTEGER,
    nft_transfer_count INTEGER,
    nft_721_transfer_count INTEGER,
    nft_1155_transfer_count INTEGER,
    PRIMARY KEY (address, block_date)
);

CREATE TABLE IF NOT EXISTS af_index_na_scheduled_metadata (
    id SERIAL NOT NULL,
    dag_id VARCHAR,
    execution_date TIMESTAMP WITHOUT TIME ZONE,
    last_data_timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS af_index_stats (
    address BYTEA NOT NULL,
    transaction_in_count INTEGER,
    transaction_out_count INTEGER,
    transaction_self_count INTEGER,
    transaction_in_value NUMERIC,
    transaction_out_value NUMERIC,
    transaction_self_value NUMERIC,
    transaction_in_fee NUMERIC,
    transaction_out_fee NUMERIC,
    transaction_self_fee NUMERIC,
    internal_transaction_in_count INTEGER,
    internal_transaction_out_count INTEGER,
    internal_transaction_self_count INTEGER,
    internal_transaction_in_value NUMERIC,
    internal_transaction_out_value NUMERIC,
    internal_transaction_self_value NUMERIC,
    erc20_transfer_in_count INTEGER,
    erc20_transfer_out_count INTEGER,
    erc20_transfer_self_count INTEGER,
    nft_transfer_in_count INTEGER,
    nft_transfer_out_count INTEGER,
    nft_transfer_self_count INTEGER,
    nft_721_transfer_in_count INTEGER,
    nft_721_transfer_out_count INTEGER,
    nft_721_transfer_self_count INTEGER,
    nft_1155_transfer_in_count INTEGER,
    nft_1155_transfer_out_count INTEGER,
    nft_1155_transfer_self_count INTEGER,
    contract_creation_count INTEGER,
    contract_destruction_count INTEGER,
    contract_operation_count INTEGER,
    transaction_count INTEGER,
    internal_transaction_count INTEGER,
    erc20_transfer_count INTEGER,
    nft_transfer_count INTEGER,
    nft_721_transfer_count INTEGER,
    nft_1155_transfer_count INTEGER,
    tag VARCHAR,
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS af_index_token_address_daily_stats (
    address BYTEA NOT NULL,
    token_holder_count INTEGER,
    token_transfer_count INTEGER,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS af_index_token_address_stats (
    address BYTEA NOT NULL,
    token_holder_count INTEGER,
    token_transfer_count INTEGER,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS af_stats_na_daily_addresses (
    block_date DATE NOT NULL,
    active_address_cnt BIGINT,
    receiver_address_cnt BIGINT,
    sender_address_cnt BIGINT,
    total_address_cnt BIGINT,
    new_address_cnt BIGINT,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS af_stats_na_daily_blocks (
    block_date DATE NOT NULL,
    cnt BIGINT,
    avg_size NUMERIC,
    avg_gas_limit NUMERIC,
    avg_gas_used NUMERIC,
    total_gas_used BIGINT,
    avg_gas_used_percentage NUMERIC,
    avg_txn_cnt NUMERIC,
    total_cnt BIGINT,
    block_interval NUMERIC,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS af_stats_na_daily_bridge_transactions (
    block_date DATE NOT NULL,
    deposit_cnt BIGINT,
    withdraw_cnt BIGINT,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS af_stats_na_daily_tokens (
    block_date DATE NOT NULL,
    erc20_active_address_cnt INTEGER,
    erc20_total_transfer_cnt BIGINT,
    erc721_active_address_cnt INTEGER,
    erc721_total_transfer_cnt BIGINT,
    erc1155_active_address_cnt INTEGER,
    erc1155_total_transfer_cnt BIGINT,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS af_stats_na_daily_transactions (
    block_date DATE NOT NULL,
    cnt BIGINT,
    total_cnt BIGINT,
    txn_error_cnt BIGINT,
    avg_transaction_fee NUMERIC,
    avg_gas_price NUMERIC,
    max_gas_price NUMERIC,
    min_gas_price NUMERIC,
    avg_receipt_l1_fee NUMERIC,
    max_receipt_l1_fee NUMERIC,
    min_receipt_l1_fee NUMERIC,
    avg_receipt_l1_gas_price NUMERIC,
    max_receipt_l1_gas_price NUMERIC,
    min_receipt_l1_gas_price NUMERIC,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS coin_prices (
    block_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    price NUMERIC,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS scheduled_metadata (
    id SERIAL NOT NULL,
    dag_id VARCHAR,
    execution_date TIMESTAMP WITHOUT TIME ZONE,
    last_data_timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS daily_wallet_addresses_aggregates;

DROP TABLE IF EXISTS daily_addresses_aggregates;

DROP TABLE IF EXISTS daily_blocks_aggregates;

DROP TABLE IF EXISTS daily_tokens_aggregates;

DROP TABLE IF EXISTS scheduled_token_count_metadata;

DROP TABLE IF EXISTS scheduled_wallet_count_metadata;

DROP TABLE IF EXISTS daily_contract_interacted_aggregates;

DROP TABLE IF EXISTS daily_transactions_aggregates;

DROP TABLE IF EXISTS statistics_wallet_addresses;

UPDATE alembic_version SET version_num='3bd2e3099bae' WHERE alembic_version.version_num = 'bc23aa19668e';

COMMIT;