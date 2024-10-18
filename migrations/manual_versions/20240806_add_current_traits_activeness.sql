BEGIN;

-- Running upgrade 832fa52da346 -> b86e241b5e18

CREATE TABLE current_traits_activeness (
    block_number BIGINT NOT NULL,
    address BYTEA NOT NULL,
    value JSONB,
    create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (address)
);

UPDATE alembic_version SET version_num='b86e241b5e18' WHERE alembic_version.version_num = '832fa52da346';

COMMIT;