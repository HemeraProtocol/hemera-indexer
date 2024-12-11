BEGIN;

-- Running upgrade 8a915490914a -> b15f744e8582

CREATE TABLE IF NOT EXISTS daily_addresses_aggregates (
    block_date DATE NOT NULL,
    active_address_cnt BIGINT,
    receiver_address_cnt BIGINT,
    sender_address_cnt BIGINT,
    total_address_cnt BIGINT,
    new_address_cnt BIGINT,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS daily_blocks_aggregates (
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

CREATE TABLE IF NOT EXISTS daily_tokens_aggregates (
    block_date DATE NOT NULL,
    erc20_active_address_cnt INTEGER,
    erc20_total_transfer_cnt BIGINT,
    erc721_active_address_cnt INTEGER,
    erc721_total_transfer_cnt BIGINT,
    erc1155_active_address_cnt INTEGER,
    erc1155_total_transfer_cnt BIGINT,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS daily_transactions_aggregates (
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
    avg_receipt_l1_gas_used NUMERIC,
    max_receipt_l1_gas_used NUMERIC,
    min_receipt_l1_gas_used NUMERIC,
    avg_receipt_l1_gas_price NUMERIC,
    max_receipt_l1_gas_price NUMERIC,
    min_receipt_l1_gas_price NUMERIC,
    avg_receipt_l1_fee_scalar NUMERIC,
    max_receipt_l1_fee_scalar NUMERIC,
    min_receipt_l1_fee_scalar NUMERIC,
    PRIMARY KEY (block_date)
);

CREATE TABLE IF NOT EXISTS scheduled_token_count_metadata (
    id SERIAL NOT NULL,
    dag_id VARCHAR,
    execution_date TIMESTAMP WITHOUT TIME ZONE,
    last_data_timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS scheduled_wallet_count_metadata (
    id SERIAL NOT NULL,
    dag_id VARCHAR,
    execution_date TIMESTAMP WITHOUT TIME ZONE,
    last_data_timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS statistics_wallet_addresses (
    address BYTEA NOT NULL,
    txn_in_cnt INTEGER,
    txn_out_cnt INTEGER,
    txn_in_value NUMERIC(78),
    txn_out_value NUMERIC(78),
    internal_txn_in_cnt INTEGER,
    internal_txn_out_cnt INTEGER,
    internal_txn_in_value NUMERIC(78),
    internal_txn_out_value NUMERIC(78),
    erc20_transfer_in_cnt INTEGER,
    erc721_transfer_in_cnt INTEGER,
    erc1155_transfer_in_cnt INTEGER,
    erc20_transfer_out_cnt INTEGER,
    erc721_transfer_out_cnt INTEGER,
    erc1155_transfer_out_cnt INTEGER,
    txn_cnt INTEGER,
    internal_txn_cnt INTEGER,
    erc20_transfer_cnt INTEGER,
    erc721_transfer_cnt INTEGER,
    erc1155_transfer_cnt INTEGER,
    deposit_cnt INTEGER,
    withdraw_cnt INTEGER,
    tag VARCHAR,
    PRIMARY KEY (address)
);

CREATE TABLE IF NOT EXISTS wallet_addresses (
    address BYTEA NOT NULL,
    ens_name VARCHAR,
    PRIMARY KEY (address)
);

UPDATE alembic_version SET version_num='b15f744e8582' WHERE alembic_version.version_num = '8a915490914a';

COMMIT;