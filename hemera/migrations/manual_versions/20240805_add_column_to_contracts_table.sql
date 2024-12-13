BEGIN;

-- Running upgrade aa99dd347ef1 -> 832fa52da346

CREATE EXTENSION IF NOT EXISTS pgcrypto;;

ALTER TABLE contracts ADD COLUMN deployed_code_hash VARCHAR GENERATED ALWAYS AS (encode(digest('0x'||encode(deployed_code, 'hex'), 'sha256'), 'hex')) STORED;

ALTER TABLE contracts ADD COLUMN transaction_from_address BYTEA;

UPDATE alembic_version SET version_num='832fa52da346' WHERE alembic_version.version_num = 'aa99dd347ef1';

COMMIT;