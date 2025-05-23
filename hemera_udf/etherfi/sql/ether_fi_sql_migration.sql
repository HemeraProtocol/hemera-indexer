BEGIN;


CREATE TABLE IF NOT EXISTS "af_ether_fi_share_balances" (
    "address" bytea NOT NULL,
    "token_address" bytea NOT NULL,
    "shares" numeric,
    "block_number" int8 NOT NULL,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("address","token_address","block_number")
);


CREATE TABLE IF NOT EXISTS "af_ether_fi_position_values" (
    "block_number" int8 NOT NULL,
    "total_share" numeric,
    "total_value_out_lp" numeric,
    "total_value_in_lp" numeric,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("block_number")
);


CREATE TABLE IF NOT EXISTS "af_ether_fi_share_balances_current" (
    "address" bytea NOT NULL,
    "token_address" bytea NOT NULL,
    "shares" numeric,
    "block_number" int8 NOT NULL,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("address","token_address")
);


CREATE TABLE IF NOT EXISTS "af_ether_fi_lrt_exchange_rate" (
    "token_address" bytea NOT NULL,
    "exchange_rate" numeric,
    "block_number" int8 NOT NULL,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "reorg" bool DEFAULT false,
    PRIMARY KEY ("token_address","block_number")
);


COMMIT;