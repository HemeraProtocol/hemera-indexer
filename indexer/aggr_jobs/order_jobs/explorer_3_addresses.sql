BEGIN;

INSERT INTO daily_addresses_aggregates (block_date, active_address_cnt, receiver_address_cnt, sender_address_cnt)
SELECT
    DATE('{start_date}') AS block_date,
    COUNT(DISTINCT CASE WHEN txn_cnt > 0 THEN address END) AS active_address_cnt,
    COUNT(DISTINCT CASE WHEN txn_in_cnt > 0 THEN address END) AS receiver_address_cnt,
    COUNT(DISTINCT CASE WHEN txn_out_cnt > 0 THEN address END) AS sender_address_cnt
FROM
    daily_wallet_address_stats
WHERE
        block_date = '{start_date}'
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
            block_date <= '{start_date}'
    GROUP BY
        address
),
     NewAddresses AS (
         SELECT
             date('{start_date}') AS block_date,
             COUNT(*) AS new_address_cnt
         FROM
             FirstAppearance
         WHERE
                 first_seen_date = '{start_date}'
     )
UPDATE daily_addresses_aggregates
SET new_address_cnt = na.new_address_cnt
FROM NewAddresses na
WHERE daily_addresses_aggregates.block_date = '{start_date}' and na.block_date = '{start_date}';

UPDATE daily_addresses_aggregates
SET total_address_cnt = sub.cumulative_addresses
FROM (
         SELECT
             block_date,
             SUM(new_address_cnt) OVER (ORDER BY block_date) AS cumulative_addresses
         FROM
             daily_addresses_aggregates
         WHERE
                 block_date <= '{start_date}'
     ) AS sub
WHERE daily_addresses_aggregates.block_date = '{start_date}' and sub.block_date = '{start_date}';

SELECT * FROM daily_addresses_aggregates WHERE block_date = '{start_date}';

COMMIT;