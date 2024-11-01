BEGIN;

-- Running upgrade 2359a28d63cb -> 6c2eecd6316b

CREATE TABLE IF NOT EXISTS af_token_deposits__transactions (
    transaction_hash BYTEA NOT NULL,
    wallet_address BYTEA,
    chain_id BIGINT,
    contract_address BYTEA,
    token_address BYTEA,
    value NUMERIC(100),
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (transaction_hash)
);

CREATE INDEX af_deposits_transactions_block_number_index ON af_token_deposits__transactions (block_number DESC);

CREATE INDEX af_deposits_transactions_chain_id_index ON af_token_deposits__transactions (chain_id);

CREATE INDEX af_deposits_transactions_contract_address_index ON af_token_deposits__transactions (contract_address);

CREATE INDEX af_deposits_transactions_token_address_index ON af_token_deposits__transactions (token_address);

CREATE INDEX af_deposits_transactions_wallet_address_index ON af_token_deposits__transactions (wallet_address);

CREATE TABLE IF NOT EXISTS af_token_deposits_current (
    wallet_address BYTEA NOT NULL,
    chain_id BIGINT NOT NULL,
    contract_address BYTEA NOT NULL,
    token_address BYTEA NOT NULL,
    value NUMERIC(100),
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (wallet_address, token_address, contract_address, chain_id)
);

UPDATE alembic_version SET version_num='6c2eecd6316b' WHERE alembic_version.version_num = '2359a28d63cb';

COMMIT;