CREATE TABLE "public"."af_fourmeme_token_trade" (
    "token" bytea NOT NULL,
    "account" bytea NOT NULL,
    "block_number" int8 NOT NULL,
    "log_index" int4 NOT NULL,
    "trade_type" varchar NOT NULL,
    "price" numeric,
    "price_usd" numeric,
    "amount" numeric,
    "cost" numeric,
    "fee" numeric,
    "offers" numeric,
    "funds" numeric,
    "block_timestamp" timestamp,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    "transaction_hash" bytea,
    PRIMARY KEY ("token","account","block_number","log_index","trade_type")
);

CREATE TABLE "public"."af_fourmeme_token_create" (
    "token" bytea NOT NULL,
    "creator" bytea,
    "request_id" int8,
    "name" varchar,
    "symbol" varchar,
    "total_supply" numeric,
    "launch_time" int8,
    "launch_fee" numeric,
    "transaction_hash" bytea,
    "block_number" int8,
    "block_timestamp" timestamp,
    "create_time" timestamp DEFAULT now(),
    "update_time" timestamp DEFAULT now(),
    PRIMARY KEY ("token")
);