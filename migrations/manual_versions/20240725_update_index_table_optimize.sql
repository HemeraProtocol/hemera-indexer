BEGIN;

-- Running upgrade b15f744e8582 -> 9f2cf385645f

CREATE TABLE IF NOT EXISTS address_current_token_balances (
    address BYTEA NOT NULL,
    token_id NUMERIC(78),
    token_type VARCHAR,
    token_address BYTEA NOT NULL,
    balance NUMERIC(100),
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address, token_address, token_id)
);

CREATE INDEX current_token_balances_token_address_balance_of_index ON address_current_token_balances (token_address, balance DESC);

CREATE INDEX current_token_balances_token_address_id_balance_of_index ON address_current_token_balances (token_address, token_id, balance DESC);

DROP INDEX erc721_token_holders_token_address_balance_of_index;

DROP TABLE erc721_token_holders;

DROP INDEX erc20_token_holders_token_address_balance_of_index;

DROP TABLE erc20_token_holders;

DROP TABLE wallet_addresses;

DROP INDEX erc1155_token_holders_token_address_balance_of_index;

DROP TABLE erc1155_token_holders;

CREATE INDEX coin_balance_address_number_desc_index ON address_coin_balances (address DESC, block_number DESC);

CREATE INDEX token_balance_address_id_number_index ON address_token_balances (address, token_address, token_id DESC, block_number DESC);

ALTER TABLE blocks ADD COLUMN blob_gas_used NUMERIC(100);

ALTER TABLE blocks ADD COLUMN excess_blob_gas NUMERIC(100);

ALTER TABLE blocks ADD COLUMN traces_count BIGINT;

ALTER TABLE blocks ADD COLUMN internal_transactions_count BIGINT;

CREATE UNIQUE INDEX blocks_hash_unique_when_not_reorg ON blocks (hash) WHERE reorg = false;

CREATE UNIQUE INDEX blocks_number_unique_when_not_reorg ON blocks (number) WHERE reorg = false;

DROP INDEX internal_transactions_address_number_transaction_index;

DROP INDEX internal_transactions_block_timestamp_index;

CREATE INDEX internal_transactions_block_number_index ON contract_internal_transactions (block_number DESC);

CREATE INDEX internal_transactions_from_address_number_transaction_index ON contract_internal_transactions (from_address, block_number DESC, transaction_index DESC);

CREATE INDEX internal_transactions_number_transaction_index ON contract_internal_transactions (block_number DESC, transaction_index DESC);

CREATE INDEX internal_transactions_to_address_number_transaction_index ON contract_internal_transactions (to_address, block_number DESC, transaction_index DESC);

DROP INDEX erc1155_detail_desc_address_id_index;

ALTER TABLE erc1155_token_id_details DROP CONSTRAINT erc1155_token_id_details_pkey;

ALTER TABLE erc1155_token_id_details RENAME address TO token_address;

CREATE INDEX erc1155_detail_desc_address_id_index ON erc1155_token_id_details (token_address DESC, token_id);

ALTER TABLE erc1155_token_id_details ADD CONSTRAINT erc1155_token_id_details_pkey PRIMARY KEY (token_address, token_id);

ALTER TABLE erc1155_token_transfers ALTER COLUMN token_id SET NOT NULL;

ALTER TABLE erc1155_token_transfers ALTER COLUMN block_hash SET NOT NULL;

DROP INDEX erc1155_token_transfers_address_block_number_log_index_index;

DROP INDEX erc1155_token_transfers_block_timestamp_index;

CREATE INDEX erc1155_token_transfers_from_address_number_log_index_index ON erc1155_token_transfers (from_address, block_number DESC, log_index DESC);

CREATE INDEX erc1155_token_transfers_number_log_index ON erc1155_token_transfers (block_number DESC, log_index DESC);

CREATE INDEX erc1155_token_transfers_to_address_number_log_index_index ON erc1155_token_transfers (to_address, block_number DESC, log_index DESC);

CREATE INDEX erc1155_token_transfers_token_address_from_index ON erc1155_token_transfers (token_address, from_address);

CREATE INDEX erc1155_token_transfers_token_address_id_index ON erc1155_token_transfers (token_address, token_id);

CREATE INDEX erc1155_token_transfers_token_address_number_log_index_index ON erc1155_token_transfers (token_address, block_number DESC, log_index DESC);

CREATE INDEX erc1155_token_transfers_token_address_to_index ON erc1155_token_transfers (token_address, to_address);

ALTER TABLE erc1155_token_transfers DROP CONSTRAINT erc1155_token_transfers_pkey;

ALTER TABLE erc1155_token_transfers ADD CONSTRAINT erc1155_token_transfers_pkey PRIMARY KEY (transaction_hash, block_hash, log_index, token_id);

ALTER TABLE erc20_token_transfers ALTER COLUMN block_hash SET NOT NULL;

DROP INDEX erc20_token_transfers_address_block_number_log_index_index;

DROP INDEX erc20_token_transfers_block_timestamp_index;

CREATE INDEX erc20_token_transfers_from_address_number_log_index_index ON erc20_token_transfers (from_address, block_number DESC, log_index DESC);

CREATE INDEX erc20_token_transfers_number_log_index ON erc20_token_transfers (block_number DESC, log_index DESC);

CREATE INDEX erc20_token_transfers_to_address_number_log_index_index ON erc20_token_transfers (to_address, block_number DESC, log_index DESC);

CREATE INDEX erc20_token_transfers_token_address_from_index_index ON erc20_token_transfers (token_address, from_address);

CREATE INDEX erc20_token_transfers_token_address_number_log_index_index ON erc20_token_transfers (token_address, block_number DESC, log_index DESC);

CREATE INDEX erc20_token_transfers_token_address_to_index_index ON erc20_token_transfers (token_address, to_address);

DROP INDEX erc721_change_address_id_number_desc_index;

ALTER TABLE erc721_token_id_changes DROP CONSTRAINT erc721_token_id_changes_pkey;

ALTER TABLE erc721_token_id_changes RENAME address TO token_address;

CREATE INDEX erc721_change_address_id_number_desc_index ON erc721_token_id_changes (token_address, token_id, block_number DESC);

ALTER TABLE erc721_token_id_changes ADD CONSTRAINT erc721_token_id_changes_pkey PRIMARY KEY (token_address, token_id, block_number);

DROP INDEX erc721_detail_owner_address_id_index;

ALTER TABLE erc721_token_id_details DROP CONSTRAINT erc721_token_id_details_pkey;

ALTER TABLE erc721_token_id_details RENAME address TO token_address;

CREATE INDEX erc721_detail_owner_address_id_index ON erc721_token_id_details (token_owner DESC, token_address, token_id);

ALTER TABLE erc721_token_id_details ADD CONSTRAINT erc721_token_id_details_pkey PRIMARY KEY (token_address, token_id);

ALTER TABLE erc721_token_transfers ALTER COLUMN block_hash SET NOT NULL;

DROP INDEX erc721_token_transfers_address_block_number_log_index_index;

CREATE INDEX erc721_token_transfers_from_address_number_log_index_index ON erc721_token_transfers (from_address, block_number DESC, log_index DESC);

CREATE INDEX erc721_token_transfers_number_log_index ON erc721_token_transfers (block_number DESC, log_index DESC);

CREATE INDEX erc721_token_transfers_to_address_number_log_index_index ON erc721_token_transfers (to_address, block_number DESC, log_index DESC);

CREATE INDEX erc721_token_transfers_token_address_from_index ON erc721_token_transfers (token_address, from_address);

CREATE INDEX erc721_token_transfers_token_address_id_index ON erc721_token_transfers (token_address, token_id);

CREATE INDEX erc721_token_transfers_token_address_number_log_index_index ON erc721_token_transfers (token_address, block_number DESC, log_index DESC);

CREATE INDEX erc721_token_transfers_token_address_to_index ON erc721_token_transfers (token_address, to_address);

ALTER TABLE erc721_token_transfers DROP COLUMN token_uri;

ALTER TABLE logs ALTER COLUMN block_hash SET NOT NULL;

CREATE INDEX logs_address_topic_0_number_log_index_index ON logs (address, topic0, block_number DESC, log_index DESC);

CREATE INDEX logs_block_number_log_index_index ON logs (block_number DESC, log_index DESC);

CREATE INDEX tokens_name_index ON tokens (name);

CREATE INDEX tokens_type_holders_index ON tokens (token_type, holder_count DESC);

CREATE INDEX tokens_type_on_chain_market_cap_index ON tokens (token_type, on_chain_market_cap DESC);

DROP INDEX traces_address_block_timestamp_index;

CREATE INDEX traces_block_number_index ON traces (block_number DESC);

CREATE INDEX traces_from_address_block_number_index ON traces (from_address, block_number DESC);

CREATE INDEX traces_to_address_block_number_index ON traces (to_address, block_number DESC);

ALTER TABLE transactions ADD COLUMN method_id VARCHAR GENERATED ALWAYS AS (substr(input :: pg_catalog.varchar, 3, 8)) STORED;

DROP INDEX transactions_address_block_number_transaction_idx;

DROP INDEX transactions_block_timestamp_block_number_index;

CREATE INDEX transactions_block_number_transaction_index ON transactions (block_number DESC, transaction_index DESC);

CREATE INDEX transactions_block_timestamp_index ON transactions (block_timestamp);

CREATE INDEX transactions_from_address_block_number_transaction_idx ON transactions (from_address ASC, block_number DESC, transaction_index DESC);

CREATE INDEX transactions_to_address_block_number_transaction_idx ON transactions (to_address ASC, block_number DESC, transaction_index DESC);

UPDATE alembic_version SET version_num='9f2cf385645f' WHERE alembic_version.version_num = 'b15f744e8582';


COMMIT;