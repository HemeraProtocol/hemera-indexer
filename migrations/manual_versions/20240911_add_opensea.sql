BEGIN;

-- Running upgrade e8f78802f27a -> 3dd9b90d2e31

CREATE TABLE af_opensea__transactions (
    address BYTEA NOT NULL,
    is_offer BOOLEAN NOT NULL,
    related_address BYTEA,
    transaction_type SMALLINT,
    order_hash BYTEA,
    zone BYTEA,
    offer JSONB,
    consideration JSONB,
    fee JSONB,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    transaction_hash BYTEA,
    block_number BIGINT NOT NULL,
    log_index BIGINT NOT NULL,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    block_hash BYTEA NOT NULL,
    reorg BOOLEAN DEFAULT false,
    protocol_version VARCHAR DEFAULT '1.6',
    PRIMARY KEY (address, is_offer, block_number, log_index, block_hash)
);

CREATE INDEX af_opensea__transactions_address_block_number_log_index_blo_idx ON af_opensea__transactions (address, block_number DESC, log_index DESC, block_timestamp DESC);

CREATE INDEX af_opensea__transactions_address_block_timestamp_idx ON af_opensea__transactions (address, block_timestamp DESC);

CREATE INDEX af_opensea__transactions_block_timestamp_idx ON af_opensea__transactions (block_timestamp DESC);

CREATE TABLE af_opensea_daily_transactions (
    address BYTEA NOT NULL,
    block_date DATE NOT NULL,
    buy_txn_count INTEGER,
    sell_txn_count INTEGER,
    swap_txn_count INTEGER,
    buy_opensea_order_count INTEGER,
    sell_opensea_order_count INTEGER,
    swap_opensea_order_count INTEGER,
    buy_nft_stats JSONB,
    sell_nft_stats JSONB,
    buy_volume_crypto JSONB,
    sell_volume_crypto JSONB,
    buy_volume_usd NUMERIC,
    sell_volume_usd NUMERIC,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address, block_date)
);

CREATE TABLE af_opensea_na_crypto_token_mapping (
    id SERIAL NOT NULL,
    address_var VARCHAR(42),
    price_symbol VARCHAR,
    decimals INTEGER DEFAULT 18 NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE af_opensea_na_orders (
    order_hash BYTEA,
    zone BYTEA,
    offerer BYTEA,
    recipient BYTEA,
    offer JSON,
    consideration JSON,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    transaction_hash BYTEA,
    block_number BIGINT NOT NULL,
    log_index INTEGER NOT NULL,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    block_hash BYTEA NOT NULL,
    reorg BOOLEAN DEFAULT false,
    protocol_version VARCHAR DEFAULT '1.6',
    PRIMARY KEY (block_number, log_index, block_hash)
);

CREATE INDEX idx_order_hash ON af_opensea_na_orders (order_hash);

CREATE TABLE af_opensea_na_scheduled_metadata (
    id SERIAL NOT NULL,
    dag_id VARCHAR,
    execution_date TIMESTAMP WITHOUT TIME ZONE,
    last_data_timestamp TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

CREATE TABLE af_opensea_profile (
    address BYTEA NOT NULL,
    buy_txn_count INTEGER DEFAULT 0,
    sell_txn_count INTEGER DEFAULT 0,
    swap_txn_count INTEGER DEFAULT 0,
    buy_opensea_order_count INTEGER DEFAULT 0,
    sell_opensea_order_count INTEGER DEFAULT 0,
    swap_opensea_order_count INTEGER DEFAULT 0,
    buy_nft_stats JSONB,
    sell_nft_stats JSONB,
    buy_volume_usd NUMERIC,
    sell_volume_usd NUMERIC,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    first_transaction_hash BYTEA,
    first_block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    txn_count INTEGER GENERATED ALWAYS AS ((buy_txn_count + sell_txn_count) + swap_txn_count) STORED,
    opensea_order_count INTEGER GENERATED ALWAYS AS ((buy_opensea_order_count + sell_opensea_order_count) + swap_opensea_order_count) STORED,
    volume_usd NUMERIC DEFAULT 0,
    PRIMARY KEY (address)
);

UPDATE alembic_version SET version_num='3dd9b90d2e31' WHERE alembic_version.version_num = 'e8f78802f27a';


COMMIT;