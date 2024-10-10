
begin ;

delete from daily_transactions_aggregates where block_date <= '{start_date}';
-- daily_transactions_aggregates
INSERT INTO daily_transactions_aggregates
SELECT
    date_trunc('day', block_timestamp) AS block_date,
    COUNT(*) AS cnt,
    SUM(COUNT(*)) OVER (ORDER BY date_trunc('day', block_timestamp)) AS total_cnt,
    SUM(CASE WHEN exist_error = true THEN 1 ELSE 0 END) AS txn_error_cnt,
    AVG(receipt_effective_gas_price * receipt_gas_used) AS avg_transaction_fee,
    AVG(gas_price) AS avg_gas_price,
    MAX(gas_price) AS max_gas_price,
    MIN(gas_price) AS min_gas_price,
    AVG(receipt_l1_fee) AS avg_receipt_l1_fee,
    MAX(receipt_l1_fee) AS max_receipt_l1_fee,
    MIN(receipt_l1_fee) AS min_receipt_l1_fee,
    AVG(receipt_l1_gas_used) AS avg_receipt_l1_gas_used,
    MAX(receipt_l1_gas_used) AS max_receipt_l1_gas_used,
    MIN(receipt_l1_gas_used) AS min_receipt_l1_gas_used,
    AVG(receipt_l1_gas_price) AS avg_receipt_l1_gas_price,
    MAX(receipt_l1_gas_price) AS max_receipt_l1_gas_price,
    MIN(receipt_l1_gas_price) AS min_receipt_l1_gas_price,
    AVG(receipt_l1_fee_scalar) AS avg_receipt_l1_fee_scalar,
    MAX(receipt_l1_fee_scalar) AS max_receipt_l1_fee_scalar,
    MIN(receipt_l1_fee_scalar) AS min_receipt_l1_fee_scalar
FROM
    transactions
    where date_trunc('day', block_timestamp) <= '{start_date}'
GROUP BY
    date_trunc('day', block_timestamp)
ORDER BY
    date_trunc('day', block_timestamp);
commit ;

begin ;

delete from daily_blocks_aggregates where block_date <= '{start_date}';

-- daily_blocks_aggregates
WITH block_data AS (
    SELECT
        size,
        gas_limit::numeric AS gas_limit,
        gas_used::numeric AS gas_used,
        transactions_count,
        EXTRACT(EPOCH FROM (lead(timestamp) OVER (ORDER BY timestamp) - timestamp)) AS block_interval,
        timestamp
    FROM
        blocks
        where date_trunc('day', timestamp) <= '{start_date}'
), daily_aggregates AS (
    SELECT
        date_trunc('day', timestamp) AS block_date,
        COUNT(*) AS cnt,
        AVG(size) AS avg_size,
        AVG(gas_limit) AS avg_gas_limit,
        AVG(gas_used) AS avg_gas_used,
        SUM(gas_used::bigint) AS total_gas_used,
        AVG((gas_used / gas_limit) * 100) AS avg_gas_used_percentage,
        AVG(transactions_count::numeric) AS avg_txn_cnt,
        SUM(COUNT(*)) OVER (ORDER BY date_trunc('day', timestamp)) AS total_cnt,
        AVG(block_interval) AS block_interval
    FROM
        block_data
    GROUP BY
        block_date
)
INSERT INTO daily_blocks_aggregates (
    block_date,
    cnt,
    avg_size,
    avg_gas_limit,
    avg_gas_used,
    total_gas_used,
    avg_gas_used_percentage,
    avg_txn_cnt,
    total_cnt,
    block_interval
)
select * from daily_aggregates
ORDER BY block_date;
commit;


begin;
delete from daily_addresses_aggregates where block_date <= '{start_date}';

-- daily-address
INSERT INTO daily_addresses_aggregates
WITH daily_address_stats AS (
    SELECT
        date_trunc('day', block_timestamp) AS block_date,
        from_address,
        to_address,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY from_address ORDER BY block_timestamp) = 1 THEN 1 ELSE 0 END AS is_new_sender,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY to_address ORDER BY block_timestamp) = 1 THEN 1 ELSE 0 END AS is_new_receiver
    FROM
        transactions
            where date_trunc('day', block_timestamp) <= '{start_date}'
),
address_counts AS (
    SELECT
        block_date,
        COUNT(DISTINCT from_address) AS sender_count,
        COUNT(DISTINCT to_address) AS receiver_count,
        COUNT(DISTINCT COALESCE(from_address, to_address)) AS active_count,
        SUM(is_new_sender) + SUM(is_new_receiver) AS new_address_count
    FROM
        daily_address_stats
    GROUP BY
        block_date
),
cumulative_counts AS (
    SELECT
        block_date,
        SUM(new_address_count) OVER (ORDER BY block_date) AS total_address_count
    FROM
        address_counts
)
SELECT
    ac.block_date,
    ac.active_count AS active_address_cnt,
    ac.receiver_count AS receiver_address_cnt,
    ac.sender_count AS sender_address_cnt,
    cc.total_address_count AS total_address_cnt,
    ac.new_address_count AS new_address_cnt
FROM
    address_counts ac
JOIN
    cumulative_counts cc ON ac.block_date = cc.block_date
ORDER BY
    ac.block_date;
commit ;

begin ;
delete from daily_tokens_aggregates where block_date <= '{start_date}';
INSERT INTO daily_tokens_aggregates
WITH erc20_stats AS (
    SELECT
        date_trunc('day', block_timestamp) AS block_date,
        COUNT(*) AS transfer_count,
        COUNT(DISTINCT from_address) + COUNT(DISTINCT to_address) AS active_address_count
    FROM
        erc20_token_transfers
                where date_trunc('day', block_timestamp) <= '{start_date}'
    GROUP BY
        date_trunc('day', block_timestamp)
),
erc721_stats AS (
    SELECT
        date_trunc('day', block_timestamp) AS block_date,
        COUNT(*) AS transfer_count,
        COUNT(DISTINCT from_address) + COUNT(DISTINCT to_address) AS active_address_count
    FROM
        erc721_token_transfers
                where date_trunc('day', block_timestamp) <= '{start_date}'

    GROUP BY
        date_trunc('day', block_timestamp)
),
erc1155_stats AS (
    SELECT
        date_trunc('day', block_timestamp) AS block_date,
        COUNT(*) AS transfer_count,
        COUNT(DISTINCT from_address) + COUNT(DISTINCT to_address) AS active_address_count
    FROM
        erc1155_token_transfers
                where date_trunc('day', block_timestamp) <= '{start_date}'

    GROUP BY
        date_trunc('day', block_timestamp)
),
all_dates AS (
    SELECT DISTINCT block_date FROM (
        SELECT block_date FROM erc20_stats
        UNION
        SELECT block_date FROM erc721_stats
        UNION
        SELECT block_date FROM erc1155_stats
    ) AS all_dates
),
cumulative_counts AS (
    SELECT
        ad.block_date,
        SUM(COALESCE(e20.transfer_count, 0)) OVER (ORDER BY ad.block_date) AS erc20_total_transfer_cnt,
        SUM(COALESCE(e721.transfer_count, 0)) OVER (ORDER BY ad.block_date) AS erc721_total_transfer_cnt,
        SUM(COALESCE(e1155.transfer_count, 0)) OVER (ORDER BY ad.block_date) AS erc1155_total_transfer_cnt
    FROM all_dates ad
    LEFT JOIN erc20_stats e20 ON ad.block_date = e20.block_date
    LEFT JOIN erc721_stats e721 ON ad.block_date = e721.block_date
    LEFT JOIN erc1155_stats e1155 ON ad.block_date = e1155.block_date
)
SELECT
    cc.block_date,
    COALESCE(e20.active_address_count, 0) AS erc20_active_address_cnt,
    cc.erc20_total_transfer_cnt,
    COALESCE(e721.active_address_count, 0) AS erc721_active_address_cnt,
    cc.erc721_total_transfer_cnt,
    COALESCE(e1155.active_address_count, 0) AS erc1155_active_address_cnt,
    cc.erc1155_total_transfer_cnt
FROM
    cumulative_counts cc
LEFT JOIN
    erc20_stats e20 ON cc.block_date = e20.block_date
LEFT JOIN
    erc721_stats e721 ON cc.block_date = e721.block_date
LEFT JOIN
    erc1155_stats e1155 ON cc.block_date = e1155.block_date
ORDER BY
    cc.block_date;
commit ;


WITH token_transfers AS (
    SELECT
        to_address AS token_address,
        from_address AS address
    FROM
        transactions
    WHERE
        to_address IN (SELECT address FROM tokens)
    UNION
    SELECT
        to_address AS token_address,
        to_address AS address
    FROM
        transactions
    WHERE
        to_address IN (SELECT address FROM tokens)
),
token_stats AS (
    SELECT
        token_address,
        COUNT(DISTINCT address) AS holder_count,
        COUNT(*) AS transfer_count
    FROM
        token_transfers
    GROUP BY
        token_address
)
UPDATE tokens
SET
    holder_count = ts.holder_count,
    transfer_count = ts.transfer_count,
    update_time = CURRENT_TIMESTAMP
FROM
    token_stats ts
WHERE
    tokens.address = ts.token_address;
