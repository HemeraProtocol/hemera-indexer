BEGIN;

-- Running upgrade bf51d23c852f -> 2359a28d63cb
CREATE TABLE IF NOT EXISTS IF NOT EXISTS token_hourly_prices(
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    price NUMERIC,
    PRIMARY KEY (symbol, timestamp)
);

CREATE TABLE IF NOT EXISTS IF NOT EXISTS token_prices(
    symbol VARCHAR NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    price NUMERIC,
    PRIMARY KEY (symbol, timestamp)
);

UPDATE alembic_version SET version_num='2359a28d63cb' WHERE alembic_version.version_num = 'bf51d23c852f';

COMMIT;