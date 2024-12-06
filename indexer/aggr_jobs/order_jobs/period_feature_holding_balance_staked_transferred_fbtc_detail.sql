delete
from period_feature_holding_balance_staked_transferred_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

with sbtc_config as (select distinct contract_address, token_address
                     from feature_staked_fbtc_config),

     staked_records as (select wallet_address,
                               contract_address,
                               protocol_id,
                               amount
                        from period_feature_staked_fbtc_detail_records
                        where period_date = '{start_date}'
                        union all
                        select d1.address                                                as wallet_address,
                               decode('42a856dbEBB97AbC1269EAB32f3bb40C15102819', 'hex') as contract_address,
                               'satlayer'                                                as protocol_id,
                               balance
                        from period_address_token_balances d1
                        where token_address = '\xe2c6755c10d0b61d8b11dd2851ae8266cea912dc'
                          and balance > 0),


     b_balance_table as (select d1.address,
                                d2.contract_address,
                                sum(d1.balance / pow(10, d3.decimals)) as b_balance
                         from period_address_token_balances d1
                                  inner join sbtc_config d2 on d1.token_address = d2.token_address
                                  left join tokens d3 on d2.token_address = d3.address
                         group by d1.address, d2.contract_address),


          c_in_balance_table AS (SELECT d1.from_address,
                                   d2.contract_address,
                                   SUM(d1.value / POW(10, d3.decimals)) AS in_balance
                            FROM erc20_token_transfers d1
                                     INNER JOIN feature_staked_fbtc_config d2
                                                ON d1.token_address = d2.token_address
                                                    AND d1.to_address = d2.to_address
                                     LEFT JOIN tokens d3
                                               ON d2.token_address = d3.address
                            GROUP BY 1, 2),

-- 计算转出金额（转出来的）
     c_out_balance_table AS (SELECT d1.to_address                        AS from_address, -- 这里的转出是由 to_address 发起
                                    d2.contract_address,
                                    SUM(d1.value / POW(10, d3.decimals)) AS out_balance
                             FROM erc20_token_transfers d1
                                      INNER JOIN feature_staked_fbtc_config d2
                                                 ON d1.token_address = d2.token_address
                                                     AND d1.from_address = d2.to_address -- 转出匹配条件
                                      LEFT JOIN tokens d3
                                                ON d2.token_address = d3.address
                             GROUP BY 1, 2),

-- 合并转入和转出，计算净余额
     c_balance_table AS (SELECT COALESCE(in_table.from_address, out_table.from_address)                            AS from_address,
                                COALESCE(in_table.contract_address, out_table.contract_address)                    AS contract_address,
                                greatest(COALESCE(in_table.in_balance, 0) - COALESCE(out_table.out_balance, 0),
                                         0)                                                                        AS c_balance
                         FROM c_in_balance_table in_table
                                  FULL OUTER JOIN c_out_balance_table out_table
                                                  ON in_table.from_address = out_table.from_address
                                                      AND in_table.contract_address = out_table.contract_address),

-- 同样逻辑应用到 protocol 层级
     c_in_balance_protocol_table AS (SELECT d1.from_address                      AS wallet_address,
                                            d2.contract_address,
                                            d2.to_address_protocol_id            AS protocol_id,
                                            d2.to_address,
                                            d2.token_address                     AS c_token_address,
                                            SUM(d1.value / POW(10, d3.decimals)) AS in_balance
                                     FROM erc20_token_transfers d1
                                              INNER JOIN feature_staked_fbtc_config d2
                                                         ON d1.token_address = d2.token_address
                                                             AND d1.to_address = d2.to_address
                                              LEFT JOIN tokens d3
                                                        ON d2.token_address = d3.address
                                     GROUP BY 1, 2, 3, 4, 5),

     c_out_balance_protocol_table AS (SELECT d1.to_address                        AS wallet_address,
                                             d2.contract_address,
                                             d2.to_address_protocol_id            AS protocol_id,
                                             d2.to_address,
                                             d2.token_address                     AS c_token_address,
                                             SUM(d1.value / POW(10, d3.decimals)) AS out_balance
                                      FROM erc20_token_transfers d1
                                               INNER JOIN feature_staked_fbtc_config d2
                                                          ON d1.token_address = d2.token_address
                                                              AND d1.from_address = d2.to_address
                                               LEFT JOIN tokens d3
                                                         ON d2.token_address = d3.address
                                      GROUP BY 1, 2, 3, 4, 5),

     c_balance_protocol_table AS (SELECT COALESCE(in_table.wallet_address, out_table.wallet_address)     AS wallet_address,
                                         COALESCE(in_table.contract_address, out_table.contract_address) AS contract_address,
                                         COALESCE(in_table.protocol_id, out_table.protocol_id)           AS protocol_id,
                                         COALESCE(in_table.to_address, out_table.to_address)             AS to_address,
                                         COALESCE(in_table.c_token_address, out_table.c_token_address)   AS c_token_address,
                                         greatest(COALESCE(in_table.in_balance, 0) - COALESCE(out_table.out_balance, 0),
                                                  0)                                                     AS balance
                                  FROM c_in_balance_protocol_table in_table
                                           FULL OUTER JOIN c_out_balance_protocol_table out_table
                                                           ON in_table.wallet_address = out_table.wallet_address
                                                               AND
                                                              in_table.contract_address = out_table.contract_address
                                                               AND in_table.protocol_id = out_table.protocol_id
                                                               AND in_table.to_address = out_table.to_address
                                                               AND
                                                              in_table.c_token_address = out_table.c_token_address),

     a_balance_table as (select d1.wallet_address,
                                d1.contract_address,
                                d1.protocol_id,
                                d1.amount / pow(10, d2.decimals) as a_balance,
                                d2.address                       as fbtc_token_address
                         from staked_records d1
                                  inner join tokens d2 on d2.address = '\xC96DE26018A54D51C097160568752C4E3BD6C364'),

     white_list_balance_table as (select d2.wallet_address,
                                         d1.a_balance,
                                         least(d1.a_balance, d2.balance) as balance,
                                         d2.protocol_id,
                                         d2.to_address                   as contract_address,
                                         d2.c_token_address
                                  from a_balance_table d1
                                           inner join c_balance_protocol_table d2
                                                      on d1.wallet_address = d2.wallet_address
                                                          and d1.contract_address = d2.contract_address),


     original_staked_balance_table as (select d1.*,
                                              coalesce(d2.b_balance, 0)       as b_balance,
                                              coalesce(d3.c_balance, 0)       as c_balance,
                                              d4.contract_address is not null as if_config
                                       from a_balance_table d1
                                                left join b_balance_table d2 on
                                           d1.wallet_address = d2.address and d1.contract_address = d2.contract_address
                                                left join c_balance_table d3 on d1.wallet_address = d3.from_address
                                           and d1.contract_address = d3.contract_address
                                                left join (select distinct contract_address from feature_staked_fbtc_config) d4
                                                          on d1.contract_address = d4.contract_address)
        ,
     result_table as (select date('{start_date}')                  as period_date,
                             wallet_address,
                             protocol_id,
                             contract_address,
                             'staked'                            as type,
                             fbtc_token_address                  as token_address,
                             case
                                 when if_config then greatest(least(a_balance - c_balance, b_balance), 0)
                                 else greatest(a_balance, 0) end as balance
                      from original_staked_balance_table

                      union all
                      select date('{start_date}') as period_date,
                             wallet_address,
                             protocol_id,
                             contract_address,
                             'transfer',
                             c_token_address    as token_address,
                             balance
                      from white_list_balance_table)


insert
into period_feature_holding_balance_staked_transferred_fbtc_detail(period_date, wallet_address, protocol_id,
                                                                   contract_address, staked_transferred_type,
                                                                   token_address, balance)
SELECT period_date, wallet_address, protocol_id, contract_address, type, token_address, balance
FROM result_table