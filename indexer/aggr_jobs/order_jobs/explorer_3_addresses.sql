BEGIN;

INSERT INTO daily_addresses_aggregates (block_date, active_address_cnt, receiver_address_cnt, sender_address_cnt)
SELECT
    DATE('{{ ds }}') AS block_date,
    COUNT(DISTINCT CASE WHEN txn_cnt > 0 THEN address END) AS active_address_cnt,
    COUNT(DISTINCT CASE WHEN txn_in_cnt > 0 THEN address END) AS receiver_address_cnt,
    COUNT(DISTINCT CASE WHEN txn_out_cnt > 0 THEN address END) AS sender_address_cnt
FROM
    daily_wallet_address_stats
WHERE
        block_date = '{{ ds }}'
GROUP BY
    block_date
ON CONFLICT (block_date) DO UPDATE
    SET
        active_address_cnt = EXCLUDED.active_address_cnt,
        receiver_address_cnt = EXCLUDED.receiver_address_cnt,
        sender_address_cnt = EXCLUDED.sender_address_cnt;

WITH FirstAppearance AS (
    SELECT
        address,
        MIN(block_date) AS first_seen_date
    FROM
        daily_wallet_address_stats
    WHERE
            block_date <= '{{ ds }}'
    GROUP BY
        address
),
     NewAddresses AS (
         SELECT
             date('{{ ds }}') AS block_date,
             COUNT(*) AS new_address_cnt
         FROM
             FirstAppearance
         WHERE
                 first_seen_date = '{{ ds }}'
     )
UPDATE daily_addresses_aggregates
SET new_address_cnt = na.new_address_cnt
FROM NewAddresses na
WHERE daily_addresses_aggregates.block_date = '{{ ds }}' and na.block_date = '{{ ds }}';

UPDATE daily_addresses_aggregates
SET total_address_cnt = sub.cumulative_addresses
FROM (
         SELECT
             block_date,
             SUM(new_address_cnt) OVER (ORDER BY block_date) AS cumulative_addresses
         FROM
             daily_addresses_aggregates
         WHERE
                 block_date <= '{{ ds }}'
     ) AS sub
WHERE daily_addresses_aggregates.block_date = '{{ ds }}' and sub.block_date = '{{ ds }}';

SELECT * FROM daily_addresses_aggregates WHERE block_date = '{{ ds }}';

COMMIT;