BEGIN;

CREATE TABLE cyber_address (
    address BYTEA NOT NULL,
    name VARCHAR,
    reverse_node BYTEA,
    block_number BIGINT,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address)
);

CREATE TABLE cyber_id_record (
    node BYTEA NOT NULL,
    token_id NUMERIC(100),
    label VARCHAR,
    registration TIMESTAMP WITHOUT TIME ZONE,
    address BYTEA,
    block_number BIGINT,
    cost NUMERIC(100),
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (node)
);

COMMIT;