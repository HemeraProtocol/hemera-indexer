BEGIN;

-- Running upgrade f4efa18760cc -> e8f78802f27a

CREATE TABLE IF NOT EXISTS address_nft_1155_holders (
    address BYTEA NOT NULL,
    token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    balance_of NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, token_address, token_id)
);

CREATE INDEX address_nft_1155_holders_token_address_balance_of_idx ON address_nft_1155_holders (token_address, token_id, balance_of DESC);

CREATE TABLE IF NOT EXISTS address_nft_transfers (
    address BYTEA NOT NULL,
    block_number INTEGER NOT NULL,
    log_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    block_hash BYTEA NOT NULL,
    token_address BYTEA,
    related_address BYTEA,
    transfer_type SMALLINT,
    token_id NUMERIC(100) NOT NULL,
    value NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, block_number, log_index, block_timestamp, block_hash, token_id)
);

CREATE TABLE IF NOT EXISTS address_token_holders (
    address BYTEA NOT NULL,
    token_address BYTEA NOT NULL,
    balance_of NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, token_address)
);

CREATE INDEX address_token_holders_token_address_balance_of_idx ON address_token_holders (token_address, balance_of DESC);

CREATE TABLE IF NOT EXISTS address_token_transfers (
    address BYTEA NOT NULL,
    block_number INTEGER NOT NULL,
    log_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    block_hash BYTEA NOT NULL,
    token_address BYTEA,
    related_address BYTEA,
    transfer_type SMALLINT,
    value NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, block_number, log_index, block_timestamp, block_hash)
);

CREATE TABLE IF NOT EXISTS address_transactions (
    address BYTEA NOT NULL,
    block_number INTEGER NOT NULL,
    transaction_index INTEGER NOT NULL,
    transaction_hash BYTEA,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    block_hash BYTEA,
    txn_type SMALLINT,
    related_address BYTEA,
    value NUMERIC(100),
    transaction_fee NUMERIC(100),
    receipt_status INTEGER,
    method TEXT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, block_number, transaction_index, block_timestamp)
);

CREATE INDEX address_transactions_address_block_timestamp_block_number_t_idx ON address_transactions (address, block_timestamp DESC, block_number DESC, transaction_index DESC);

CREATE INDEX address_transactions_address_txn_type_block_timestamp_block_idx ON address_transactions (address, txn_type, block_timestamp DESC, block_number DESC, transaction_index DESC);

CREATE TABLE IF NOT EXISTS token_address_nft_inventories (
    token_address BYTEA NOT NULL,
    token_id NUMERIC(100) NOT NULL,
    wallet_address BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (token_address, token_id)
);

CREATE INDEX token_address_nft_inventories_wallet_address_token_address__idx ON token_address_nft_inventories (wallet_address, token_address, token_id);

UPDATE alembic_version SET version_num='e8f78802f27a' WHERE alembic_version.version_num = 'f4efa18760cc';

COMMIT;