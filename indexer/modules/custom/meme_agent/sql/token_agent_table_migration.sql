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

COMMIT;