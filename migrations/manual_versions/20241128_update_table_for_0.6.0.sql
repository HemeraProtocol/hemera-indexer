BEGIN;

-- Running upgrade f846e3abeb18 -> 3c7ea7b95dc5

ALTER TABLE logs DROP CONSTRAINT logs_pkey;

CREATE INDEX logs_pkey ON logs (transaction_hash, block_hash, log_index);

ALTER TABLE af_holding_balance_uniswap_v3_period DROP CONSTRAINT af_holding_balance_uniswap_v3_period_pkey;

ALTER TABLE af_holding_balance_uniswap_v3_period RENAME position_token_address TO pool_address;

CREATE INDEX af_holding_balance_uniswap_v3_period_pkey ON af_holding_balance_uniswap_v3_period (period_date, protocol_id, pool_address, token_id);

UPDATE alembic_version SET version_num='f846e3abeb18' WHERE alembic_version.version_num = '3c7ea7b95dc5';

COMMIT;