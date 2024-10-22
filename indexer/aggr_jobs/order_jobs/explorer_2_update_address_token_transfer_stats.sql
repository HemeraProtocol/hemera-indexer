WITH erc20_in AS (
    SELECT
        to_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc20_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY to_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc20_transfer_in_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc20_in

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc20_transfer_in_cnt = EXCLUDED.erc20_transfer_in_cnt;


WITH erc20_out AS (
    SELECT
        from_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc20_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY from_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc20_transfer_out_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc20_out

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc20_transfer_out_cnt = EXCLUDED.erc20_transfer_out_cnt;


WITH erc721_in AS (
    SELECT
        to_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc721_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY to_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc721_transfer_in_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc721_in

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc721_transfer_in_cnt = EXCLUDED.erc721_transfer_in_cnt;


WITH erc721_out AS (
    SELECT
        from_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc721_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY from_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc721_transfer_out_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc721_out

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc721_transfer_out_cnt = EXCLUDED.erc721_transfer_out_cnt;

WITH erc1155_in AS (
    SELECT
        to_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc1155_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY to_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc1155_transfer_in_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc1155_in

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc1155_transfer_in_cnt = EXCLUDED.erc1155_transfer_in_cnt;

WITH erc1155_out AS (
    SELECT
        from_address AS address,
        DATE(block_timestamp) AS block_date,
        COUNT(1) AS cnt
    FROM erc1155_token_transfers
    WHERE DATE(block_timestamp) = DATE '{start_date}'
    GROUP BY from_address, DATE(block_timestamp)
)

INSERT INTO daily_wallet_address_stats
(address, block_date, erc1155_transfer_out_cnt)
SELECT
    address,
    block_date,
    cnt
FROM erc1155_out

ON CONFLICT (address, block_date)
    DO UPDATE SET
    erc1155_transfer_out_cnt = EXCLUDED.erc1155_transfer_out_cnt;