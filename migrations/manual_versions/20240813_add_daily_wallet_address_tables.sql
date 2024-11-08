BEGIN;

-- Running upgrade 1b1c6a8b6c7b -> bf51d23c852f

CREATE TABLE IF NOT EXISTS daily_contract_interacted_aggregates (
    block_date DATE NOT NULL,
    from_address BYTEA NOT NULL,
    to_address BYTEA NOT NULL,
    contract_interacted_cnt INTEGER,
    PRIMARY KEY (block_date, from_address, to_address)
);

CREATE TABLE IF NOT EXISTS daily_wallet_addresses_aggregates (
    address BYTEA NOT NULL,
    block_date DATE NOT NULL,
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
    internal_txn_cnt INTEGER GENERATED ALWAYS AS (internal_txn_in_cnt + internal_txn_out_cnt) STORED,
    erc20_transfer_cnt INTEGER GENERATED ALWAYS AS (erc20_transfer_in_cnt + erc20_transfer_out_cnt) STORED,
    erc721_transfer_cnt INTEGER GENERATED ALWAYS AS (erc721_transfer_in_cnt + erc721_transfer_out_cnt) STORED,
    erc1155_transfer_cnt INTEGER GENERATED ALWAYS AS (erc1155_transfer_in_cnt + erc1155_transfer_out_cnt) STORED,
    txn_self_cnt INTEGER,
    txn_in_error_cnt INTEGER,
    txn_out_error_cnt INTEGER,
    txn_self_error_cnt INTEGER,
    txn_cnt INTEGER GENERATED ALWAYS AS (((txn_in_cnt + txn_out_cnt) - txn_self_cnt)) STORED,
    deposit_cnt INTEGER,
    withdraw_cnt INTEGER,
    gas_in_used NUMERIC(78),
    l2_txn_in_fee NUMERIC(78),
    l1_txn_in_fee NUMERIC(78),
    txn_in_fee NUMERIC(78),
    gas_out_used NUMERIC(78),
    l2_txn_out_fee NUMERIC(78),
    l1_txn_out_fee NUMERIC(78),
    txn_out_fee NUMERIC(78),
    contract_deployed_cnt INTEGER,
    from_address_unique_interacted_cnt INTEGER,
    to_address_unique_interacted_cnt INTEGER,
    PRIMARY KEY (address, block_date)
);

CREATE TABLE IF NOT EXISTS period_wallet_addresses_aggregates (
    address BYTEA NOT NULL,
    period_date DATE NOT NULL,
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
    internal_txn_cnt INTEGER GENERATED ALWAYS AS (internal_txn_in_cnt + internal_txn_out_cnt) STORED,
    erc20_transfer_cnt INTEGER GENERATED ALWAYS AS (erc20_transfer_in_cnt + erc20_transfer_out_cnt) STORED,
    erc721_transfer_cnt INTEGER GENERATED ALWAYS AS (erc721_transfer_in_cnt + erc721_transfer_out_cnt) STORED,
    erc1155_transfer_cnt INTEGER GENERATED ALWAYS AS (erc1155_transfer_in_cnt + erc1155_transfer_out_cnt) STORED,
    txn_self_cnt INTEGER NOT NULL,
    txn_in_error_cnt INTEGER NOT NULL,
    txn_out_error_cnt INTEGER NOT NULL,
    txn_self_error_cnt INTEGER NOT NULL,
    txn_cnt INTEGER GENERATED ALWAYS AS (((txn_in_cnt + txn_out_cnt) - txn_self_cnt)) STORED,
    deposit_cnt INTEGER,
    withdraw_cnt INTEGER,
    gas_in_used NUMERIC(78),
    l2_txn_in_fee NUMERIC(78),
    l1_txn_in_fee NUMERIC(78),
    txn_in_fee NUMERIC(78),
    gas_out_used NUMERIC(78),
    l2_txn_out_fee NUMERIC(78),
    l1_txn_out_fee NUMERIC(78),
    txn_out_fee NUMERIC(78),
    contract_deployed_cnt INTEGER,
    from_address_unique_interacted_cnt INTEGER,
    to_address_unique_interacted_cnt INTEGER,
    PRIMARY KEY (address, period_date)
);

UPDATE alembic_version SET version_num='bf51d23c852f' WHERE alembic_version.version_num = '1b1c6a8b6c7b';

COMMIT;