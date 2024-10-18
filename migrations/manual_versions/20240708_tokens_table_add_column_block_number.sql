BEGIN;

-- Running upgrade 5e4608933f64 -> 8a915490914a

ALTER TABLE tokens ADD COLUMN block_number BIGINT;

UPDATE alembic_version SET version_num='8a915490914a' WHERE alembic_version.version_num = '5e4608933f64';

COMMIT;