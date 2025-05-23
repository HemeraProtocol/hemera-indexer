BEGIN;

CREATE TABLE IF NOT EXISTS "af_lido_position_values" (
    "block_number" int8 NOT NULL,
    "total_share" numeric,
    "buffered_eth" numeric,
    "consensus_layer" numeric,
    "deposited_validators" numeric,
    "cl_validators" numeric,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("block_number")
);

CREATE TABLE IF NOT EXISTS "af_lido_seth_share_balances" (
    "address" bytea NOT NULL,
    "token_address" bytea NOT NULL,
    "block_number" int8 NOT NULL,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    "shares" numeric,
    PRIMARY KEY ("address","token_address","block_number")
);

CREATE TABLE IF NOT EXISTS "af_lido_seth_share_balances_current" (
    "address" bytea NOT NULL,
    "token_address" bytea NOT NULL,
    "shares" numeric,
    "block_number" int8 NOT NULL,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("address","token_address")
);


COMMIT;