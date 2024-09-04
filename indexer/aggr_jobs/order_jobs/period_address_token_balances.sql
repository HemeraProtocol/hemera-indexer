INSERT INTO period_address_token_balances (address, period_date, token_address, token_id, token_type, balance)
SELECT d1.address, d1.block_date, d1.token_address, d1.token_id, d1.token_type, d1.balance
FROM daily_address_token_balances d1
where block_date = '{block_date}'
ON CONFLICT (address, period_date, token_address, token_id)
    DO UPDATE
    SET balance = EXCLUDED.balance;