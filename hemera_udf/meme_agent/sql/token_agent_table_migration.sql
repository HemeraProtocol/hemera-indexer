BEGIN;

CREATE TABLE IF NOT EXISTS af_clanker_created_token (
    "token_address" bytea NOT NULL,
    "lp_nft_id" int8,
    "deployer" bytea,
    "fid" int8,
    "name" varchar,
    "symbol" varchar,
    "supply" numeric,
    "locker_address" bytea,
    "cast_hash" bytea,
    "block_number" int8,
    "version" int8,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    "update_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("token_address")
);

CREATE TABLE IF NOT EXISTS af_virtuals_created_token (
    "virtual_id" int8 NOT NULL,
    "token" bytea,
    "dao" bytea,
    "tba" bytea,
    "ve_token" bytea,
    "lp" bytea,
    "block_number" int8,
    "block_timestamp" timestamp,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    "update_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("virtual_id")
);

CREATE TABLE IF NOT EXISTS af_larry_created_token (
    "token" bytea NOT NULL,
    "party" bytea,
    "recipient" bytea,
    "name" varchar,
    "symbol" varchar,
    "eth_value" numeric,
    "block_number" int8,
    "block_timestamp" timestamp,
    "create_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    "update_time" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("token")
);

COMMIT;