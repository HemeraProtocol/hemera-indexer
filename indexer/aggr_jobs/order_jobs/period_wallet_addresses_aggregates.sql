begin;
delete
from period_wallet_addresses_aggregates
where period_date = '{end_date}';
insert into period_wallet_addresses_aggregates(address, period_date, txn_in_cnt, txn_out_cnt, txn_in_value,
                                               txn_out_value, internal_txn_in_cnt, internal_txn_out_cnt,
                                               internal_txn_in_value, internal_txn_out_value, erc20_transfer_in_cnt,
                                               erc721_transfer_in_cnt, erc1155_transfer_in_cnt, erc20_transfer_out_cnt,
                                               erc721_transfer_out_cnt, erc1155_transfer_out_cnt, txn_self_cnt,
                                               txn_in_error_cnt, txn_out_error_cnt, txn_self_error_cnt, deposit_cnt,
                                               withdraw_cnt, gas_in_used, l2_txn_in_fee, l1_txn_in_fee, txn_in_fee,
                                               gas_out_used, l2_txn_out_fee, l1_txn_out_fee, txn_out_fee,
                                               contract_deployed_cnt, from_address_unique_interacted_cnt,
                                               to_address_unique_interacted_cnt)
WITH today_table AS (SELECT *
                     FROM daily_wallet_addresses_aggregates
                     WHERE block_date = '{start_date}'),
     yesterday_table AS (SELECT *
                         FROM period_wallet_addresses_aggregates
                         WHERE period_date = '{end_date}'),
     from_address_unique_interacted_cnt_table as (SELECT from_address               as address,
                                                         count(distinct to_address) as from_address_unique_interacted_cnt
                                                  FROM daily_contract_interacted_aggregates
                                                  group by 1),
     to_address_unique_interacted_cnt_table as (SELECT to_address                   as address,
                                                       count(distinct from_address) as to_address_unique_interacted_cnt
                                                FROM daily_contract_interacted_aggregates
                                                group by 1)

SELECT COALESCE(s1.address, s2.address)                                    AS address,
       date('{end_date}')                                                  AS block_date,
       COALESCE(s1.txn_in_cnt, 0) + COALESCE(s2.txn_in_cnt, 0)             AS txn_in_cnt,
       COALESCE(s1.txn_out_cnt, 0) + COALESCE(s2.txn_out_cnt, 0)           AS txn_out_cnt,
       COALESCE(s1.txn_in_value, 0) + COALESCE(s2.txn_in_value, 0)         AS txn_in_value,
       COALESCE(s1.txn_out_value, 0) + COALESCE(s2.txn_out_value, 0)       AS txn_out_value,
       COALESCE(s1.internal_txn_in_cnt, 0) +
       COALESCE(s2.internal_txn_in_cnt, 0)                                 AS internal_txn_in_cnt,
       COALESCE(s1.internal_txn_out_cnt, 0) +
       COALESCE(s2.internal_txn_out_cnt, 0)                                AS internal_txn_out_cnt,
       COALESCE(s1.internal_txn_in_value, 0) +
       COALESCE(s2.internal_txn_in_value, 0)                               AS internal_txn_in_value,
       COALESCE(s1.internal_txn_out_value, 0) +
       COALESCE(s2.internal_txn_out_value, 0)                              AS internal_txn_out_value,
       COALESCE(s1.erc20_transfer_in_cnt, 0) +
       COALESCE(s2.erc20_transfer_in_cnt, 0)                               AS erc20_transfer_in_cnt,
       COALESCE(s1.erc721_transfer_in_cnt, 0) +
       COALESCE(s2.erc721_transfer_in_cnt, 0)                              AS erc721_transfer_in_cnt,
       COALESCE(s1.erc1155_transfer_in_cnt, 0) +
       COALESCE(s2.erc1155_transfer_in_cnt, 0)                             AS erc1155_transfer_in_cnt,
       COALESCE(s1.erc20_transfer_out_cnt, 0) +
       COALESCE(s2.erc20_transfer_out_cnt, 0)                              AS erc20_transfer_out_cnt,
       COALESCE(s1.erc721_transfer_out_cnt, 0) +
       COALESCE(s2.erc721_transfer_out_cnt, 0)                             AS erc721_transfer_out_cnt,
       COALESCE(s1.erc1155_transfer_out_cnt, 0) +
       COALESCE(s2.erc1155_transfer_out_cnt, 0)                            AS erc1155_transfer_out_cnt,
       COALESCE(s1.txn_self_cnt, 0) + COALESCE(s2.txn_self_cnt, 0)         AS txn_self_cnt,
       COALESCE(s1.txn_in_error_cnt, 0) + COALESCE(s2.txn_in_error_cnt, 0) AS txn_in_error_cnt,
       COALESCE(s1.txn_out_error_cnt, 0) +
       COALESCE(s2.txn_out_error_cnt, 0)                                   AS txn_out_error_cnt,
       COALESCE(s1.txn_self_error_cnt, 0) +
       COALESCE(s2.txn_self_error_cnt, 0)                                  AS txn_self_error_cnt,
       COALESCE(s1.deposit_cnt, 0) + COALESCE(s2.deposit_cnt, 0)           AS deposit_cnt,
       COALESCE(s1.withdraw_cnt, 0) + COALESCE(s2.withdraw_cnt, 0)         AS withdraw_cnt,
       COALESCE(s1.gas_in_used, 0) + COALESCE(s2.gas_in_used, 0)           AS gas_in_used,
       COALESCE(s1.l2_txn_in_fee, 0) + COALESCE(s2.l2_txn_in_fee, 0)       AS l2_txn_in_fee,
       COALESCE(s1.l1_txn_in_fee, 0) + COALESCE(s2.l1_txn_in_fee, 0)       AS l1_txn_in_fee,
       COALESCE(s1.txn_in_fee, 0) + COALESCE(s2.txn_in_fee, 0)             AS txn_in_fee,
       COALESCE(s1.gas_out_used, 0) + COALESCE(s2.gas_out_used, 0)         AS gas_out_used,
       COALESCE(s1.l2_txn_out_fee, 0) + COALESCE(s2.l2_txn_out_fee, 0)     AS l2_txn_out_fee,
       COALESCE(s1.l1_txn_out_fee, 0) + COALESCE(s2.l1_txn_out_fee, 0)     AS l1_txn_out_fee,
       COALESCE(s1.txn_out_fee, 0) + COALESCE(s2.txn_out_fee, 0)           AS txn_out_fee,
       COALESCE(s1.contract_deployed_cnt, 0) +
       COALESCE(s2.contract_deployed_cnt, 0)                               AS contract_deployed_cnt,
       COALESCE(s1.from_address_unique_interacted_cnt, 0) +
       COALESCE(s2.from_address_unique_interacted_cnt, 0)                  AS from_address_unique_interacted_cnt,
       COALESCE(s1.to_address_unique_interacted_cnt, 0) +
       COALESCE(s2.to_address_unique_interacted_cnt, 0)                    AS to_address_unique_interacted_cnt
FROM today_table s1
         FULL JOIN yesterday_table s2 ON s1.address = s2.address
         left join from_address_unique_interacted_cnt_table s3 on coalesce(s1.address, s2.address) = s3.address
         left join to_address_unique_interacted_cnt_table s4 on coalesce(s1.address, s2.address) = s4.address;
commit