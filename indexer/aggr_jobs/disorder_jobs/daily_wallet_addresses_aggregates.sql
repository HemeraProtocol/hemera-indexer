Begin;
-- Handle outgoing transactions including errors
WITH out_txn AS (SELECT from_address                                        AS address,
                        DATE(block_timestamp)                               AS block_date,
                        COUNT(DISTINCT hash)                                AS txn_out_cnt,
                        SUM(value)                                          AS txn_out_value,
                        SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_out_error_cnt
                 FROM transactions
                 WHERE from_address is not null
                   and block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                 GROUP BY from_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, txn_out_cnt, txn_out_value, txn_out_error_cnt)
SELECT address,
       block_date,
       txn_out_cnt,
       txn_out_value,
       txn_out_error_cnt
FROM out_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET txn_out_cnt       = EXCLUDED.txn_out_cnt,
                  txn_out_value     = EXCLUDED.txn_out_value,
                  txn_out_error_cnt = EXCLUDED.txn_out_error_cnt;

-- Handle incoming transactions including errors
WITH in_txn AS (SELECT to_address                                          AS address,
                       DATE(block_timestamp)                               AS block_date,
                       COUNT(DISTINCT hash)                                AS txn_in_cnt,
                       SUM(value)                                          AS txn_in_value,
                       SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_in_error_cnt
                FROM transactions
                WHERE to_address is not null
                  and block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                GROUP BY to_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, txn_in_cnt, txn_in_value, txn_in_error_cnt)
SELECT address,
       block_date,
       txn_in_cnt,
       txn_in_value,
       txn_in_error_cnt
FROM in_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET txn_in_cnt       = EXCLUDED.txn_in_cnt,
                  txn_in_value     = EXCLUDED.txn_in_value,
                  txn_in_error_cnt = EXCLUDED.txn_in_error_cnt;


-- Handle self transactions including errors
WITH self_txn AS (SELECT from_address                                        AS address,
                         DATE(block_timestamp)                               AS block_date,
                         COUNT(DISTINCT hash)                                AS txn_self_cnt,
                         SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) AS txn_self_error_cnt
                  FROM transactions
                  WHERE from_address = to_address
                    and from_address is not null
                    and block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                  GROUP BY from_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, txn_self_cnt, txn_self_error_cnt)
SELECT address,
       block_date,
       txn_self_cnt,
       txn_self_error_cnt
FROM self_txn

ON CONFLICT (address, block_date)
    DO UPDATE SET txn_self_cnt       = EXCLUDED.txn_self_cnt,
                  txn_self_error_cnt = EXCLUDED.txn_self_error_cnt;

WITH erc20_in AS (SELECT to_address            AS address,
                         DATE(block_timestamp) AS block_date,
                         COUNT(1)              AS cnt
                  FROM erc20_token_transfers
                  WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                  GROUP BY to_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc20_transfer_in_cnt)
SELECT address,
       block_date,
       cnt
FROM erc20_in

ON CONFLICT (address, block_date)
    DO UPDATE SET erc20_transfer_in_cnt = EXCLUDED.erc20_transfer_in_cnt;


WITH erc20_out AS (SELECT from_address          AS address,
                          DATE(block_timestamp) AS block_date,
                          COUNT(1)              AS cnt
                   FROM erc20_token_transfers
                   WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                   GROUP BY from_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc20_transfer_out_cnt)
SELECT address,
       block_date,
       cnt
FROM erc20_out

ON CONFLICT (address, block_date)
    DO UPDATE SET erc20_transfer_out_cnt = EXCLUDED.erc20_transfer_out_cnt;


WITH erc721_in AS (SELECT to_address            AS address,
                          DATE(block_timestamp) AS block_date,
                          COUNT(1)              AS cnt
                   FROM erc721_token_transfers
                   WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                   GROUP BY to_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc721_transfer_in_cnt)
SELECT address,
       block_date,
       cnt
FROM erc721_in

ON CONFLICT (address, block_date)
    DO UPDATE SET erc721_transfer_in_cnt = EXCLUDED.erc721_transfer_in_cnt;


WITH erc721_out AS (SELECT from_address          AS address,
                           DATE(block_timestamp) AS block_date,
                           COUNT(1)              AS cnt
                    FROM erc721_token_transfers
                    WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                    GROUP BY from_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc721_transfer_out_cnt)
SELECT address,
       block_date,
       cnt
FROM erc721_out

ON CONFLICT (address, block_date)
    DO UPDATE SET erc721_transfer_out_cnt = EXCLUDED.erc721_transfer_out_cnt;

WITH erc1155_in AS (SELECT to_address            AS address,
                           DATE(block_timestamp) AS block_date,
                           COUNT(1)              AS cnt
                    FROM erc1155_token_transfers
                    WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                    GROUP BY to_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc1155_transfer_in_cnt)
SELECT address,
       block_date,
       cnt
FROM erc1155_in

ON CONFLICT (address, block_date)
    DO UPDATE SET erc1155_transfer_in_cnt = EXCLUDED.erc1155_transfer_in_cnt;

WITH erc1155_out AS (SELECT from_address          AS address,
                            DATE(block_timestamp) AS block_date,
                            COUNT(1)              AS cnt
                     FROM erc1155_token_transfers
                     WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                     GROUP BY from_address, DATE(block_timestamp))

INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, erc1155_transfer_out_cnt)
SELECT address,
       block_date,
       cnt
FROM erc1155_out

ON CONFLICT (address, block_date)
    DO UPDATE SET erc1155_transfer_out_cnt = EXCLUDED.erc1155_transfer_out_cnt;

with contract_deployed_table as (select transaction_from_address as address,
                                        date(block_timestamp)    as block_date,
                                        count(1)                 as contract_deployed_cnt
                                 from contracts
                                 WHERE block_timestamp >= '{start_date}'
                      and block_timestamp < '{end_date}'
                                 group by 1, 2)
INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, contract_deployed_cnt)
SELECT address,
       block_date,
       contract_deployed_cnt
FROM contract_deployed_table

ON CONFLICT (address, block_date)
    DO UPDATE SET contract_deployed_cnt = EXCLUDED.contract_deployed_cnt;

--
with contract_interacted_detail_table as (
select date(d2.block_timestamp) as block_date, from_address, to_address, count(1) as contract_interacted_cnt
from contracts d1
         inner join transactions d2
                    on d1.address = d2.to_address
WHERE d2.block_timestamp >= '{start_date}' and d2.block_timestamp < '{end_date}'
group by 1, 2, 3
)

insert into daily_contract_interacted_aggregates(block_date, from_address, to_address, contract_interacted_cnt)
select
    block_date, from_address, to_address, contract_interacted_cnt
from  contract_interacted_detail_table
ON CONFLICT (block_date, from_address, to_address)
    DO UPDATE SET contract_interacted_cnt = EXCLUDED.contract_interacted_cnt;
    ;


INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, from_address_unique_interacted_cnt)
SELECT from_address as address,
       block_date,
       count(1) as from_address_unique_interacted_cnt
FROM daily_contract_interacted_aggregates
group by 1,2
ON CONFLICT (address, block_date)
    DO UPDATE SET from_address_unique_interacted_cnt = EXCLUDED.from_address_unique_interacted_cnt;



INSERT
INTO daily_wallet_addresses_aggregates
    (address, block_date, to_address_unique_interacted_cnt)
SELECT to_address as address,
       block_date,
       count(1) as from_address_unique_interacted_cnt
FROM daily_contract_interacted_aggregates
group by 1,2
ON CONFLICT (address, block_date)
    DO UPDATE SET to_address_unique_interacted_cnt = EXCLUDED.to_address_unique_interacted_cnt;
commit