BEGIN;

-- Running upgrade 67015d9fa59b -> bc23aa19668e

ALTER TABLE af_ens_node_current ADD COLUMN block_number BIGINT;

UPDATE alembic_version SET version_num='bc23aa19668e' WHERE alembic_version.version_num = '67015d9fa59b';

COMMIT;