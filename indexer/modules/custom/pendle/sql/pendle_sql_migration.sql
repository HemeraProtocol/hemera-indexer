BEGIN;



CREATE TABLE IF NOT EXISTS "af_pendle_pool" (
    "market_address" bytea NOT NULL,
    "sy_address" bytea,
    "pt_address" bytea,
    "yt_address" bytea,
    "block_number" int8,
    "chain_id" int8,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    "underlying_asset" bytea,
    PRIMARY KEY ("market_address")
);

CREATE TABLE IF NOT EXISTS "af_pendle_user_active_balance" (
    "market_address" bytea NOT NULL,
    "user_address" bytea NOT NULL,
    "sy_balance" numeric,
    "active_balance" numeric,
    "total_active_supply" numeric,
    "market_sy_balance" numeric,
    "block_number" int8 NOT NULL,
    "chain_id" int8,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("market_address","user_address","block_number")
);

CREATE TABLE IF NOT EXISTS "af_pendle_user_active_balance_current" (
    "market_address" bytea NOT NULL,
    "user_address" bytea NOT NULL,
    "sy_balance" numeric,
    "active_balance" numeric,
    "total_active_supply" numeric,
    "market_sy_balance" numeric,
    "block_number" int8 NOT NULL,
    "chain_id" int8,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    "update_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("market_address","user_address")
);


COMMIT;