-- Handle outgoing transactions including errors
WITH out_txn AS (
    SELECT
        from_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(DISTINCT hash) AS txn_out_cnt,
        SUM(value) AS txn_out_value,
        SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_out_error_cnt
    FROM transactions
    WHERE block_timestamp >= '{{ ds }}' AND block_timestamp < '{{ ds }}'::DATE + INTERVAL '1 DAY'
      and from_address is not null
    GROUP BY from_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, txn_out_cnt, txn_out_value, txn_out_error_cnt)
SELECT
    address,
    block_date,
    txn_out_cnt,
    txn_out_value,
    txn_out_error_cnt
FROM out_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET
                  txn_out_cnt = EXCLUDED.txn_out_cnt,
                  txn_out_value = EXCLUDED.txn_out_value,
                  txn_out_error_cnt = EXCLUDED.txn_out_error_cnt;

-- Handle incoming transactions including errors
WITH in_txn AS (
    SELECT
        to_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(DISTINCT hash) AS txn_in_cnt,
        SUM(value) AS txn_in_value,
        SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_in_error_cnt
    FROM transactions
    WHERE block_timestamp >= '{{ ds }}' AND block_timestamp < '{{ ds }}'::DATE + INTERVAL '1 DAY'
      and to_address is not null
    GROUP BY to_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, txn_in_cnt, txn_in_value, txn_in_error_cnt)
SELECT
    address,
    block_date,
    txn_in_cnt,
    txn_in_value,
    txn_in_error_cnt
FROM in_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET
                  txn_in_cnt = EXCLUDED.txn_in_cnt,
                  txn_in_value = EXCLUDED.txn_in_value,
                  txn_in_error_cnt = EXCLUDED.txn_in_error_cnt;


-- Handle self transactions including errors
WITH self_txn AS (
    SELECT
        from_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(DISTINCT hash) AS txn_self_cnt,
        SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_self_error_cnt
    FROM transactions
    WHERE block_timestamp >= '{{ ds }}' AND block_timestamp < '{{ ds }}'::DATE + INTERVAL '1 DAY'
      and from_address = to_address and from_address is not null
    GROUP BY from_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, txn_self_cnt, txn_self_error_cnt)
SELECT
    address,
    block_date,
    txn_self_cnt,
    txn_self_error_cnt
FROM self_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET
                  txn_self_cnt = EXCLUDED.txn_self_cnt,
                  txn_self_error_cnt = EXCLUDED.txn_self_error_cnt;