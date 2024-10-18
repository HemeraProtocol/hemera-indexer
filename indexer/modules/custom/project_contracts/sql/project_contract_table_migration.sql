BEGIN;

CREATE TABLE af_project_contracts (
    project_id VARCHAR,
    chain_id INTEGER,
    address BYTEA NOT NULL,
    deployer BYTEA,
    transaction_from_address BYTEA,
    trace_creator BYTEA,
    block_number BIGINT,
    block_timestamp TIMESTAMP WITHOUT TIME ZONE,
    transaction_hash BYTEA,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    reorg BOOLEAN DEFAULT false,
    PRIMARY KEY (address)
);

CREATE TABLE af_projects (
    project_id VARCHAR NOT NULL,
    name VARCHAR,
    deployer BYTEA NOT NULL,
    address_type INTEGER,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (project_id, deployer)
);

COMMENT ON COLUMN af_projects.address_type IS '0是作为deploy地址不参与统计；1参与统计';

COMMIT;