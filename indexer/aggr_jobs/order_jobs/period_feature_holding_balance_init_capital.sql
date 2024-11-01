delete
from period_feature_holding_balance_init_capital
where period_date = '{start_date}';

with vc_table as (select pow(10, 8) as VIRTUAL_SHARES, 1 as VIRTUAL_ASSETS),
     period_position_table as (select *
                               from (select *,
                                            row_number() over (partition by position_id order by block_number desc) rn
                                     from init_capital_position_history
                                     where block_timestamp < '{end_date}') t
                               where rn = 1),
     period_pool_table as (select *
                           from (select *, row_number() over (partition by pool_address order by block_number desc) rn
                                 from init_capital_pool_history
                                 where block_timestamp < '{end_date}') t
                           where rn = 1),

     collaterals_table as (SELECT position_id,
                                  viewer_address                          as wallet_address,
                                  CAST(pool_data ->> 'amount' AS NUMERIC) AS amount,
                                  pool_data ->> 'pool_address'            AS pool_address,
                                  pool_data ->> 'token_address'           AS token_address
                           FROM period_position_table,
                                LATERAL jsonb_array_elements(collaterals) AS pool_data
                           WHERE jsonb_typeof(collaterals) = 'array'
                             and pool_data ->> 'amount' > '0'),
     deposit_table as (select d1.wallet_address,
                              d1.position_id,
                              d2.pool_address,
                              d2.token_address,
                              d3.symbol            as token_symbol,
                              d1.amount * (d2.total_asset + VIRTUAL_ASSETS) / (d2.total_supply + VIRTUAL_SHARES) /
                              pow(10, d3.decimals) as deposit_balance
                       from collaterals_table d1
                                inner join period_pool_table d2
                                           on d1.pool_address = concat('0x', encode(d2.pool_address, 'hex'))
                                inner join tokens d3 on d2.token_address = d3.address,
                            vc_table),
     borrows_table as (SELECT position_id,
                              viewer_address                         as wallet_address,
                              CAST(pool_data ->> 'share' AS NUMERIC) AS share,
                              pool_data ->> 'pool_address'           AS pool_address,
                              pool_data ->> 'token_address'          AS token_address
                       FROM period_position_table,
                            LATERAL jsonb_array_elements(borrows) AS pool_data
                       WHERE jsonb_typeof(borrows) = 'array'
                         and pool_data ->> 'share' > '0'),

     borrow_table as (select d1.wallet_address,
                             d1.position_id,
                             d2.pool_address,
                             d2.token_address,
                             d3.symbol                                                             as token_symbol,
                             d1.share * d2.total_debt / d2.total_debt_share / pow(10, d3.decimals) as borrow_balance
                      from borrows_table d1
                               inner join period_pool_table d2
                                          on d1.pool_address = concat('0x', encode(d2.pool_address, 'hex'))
                               inner join tokens d3 on d2.token_address = d3.address)


insert
into period_feature_holding_balance_init_capital(period_date, protocol_id, position_id, wallet_address,
                                                 contract_address, token_address, deposit_borrow_type, token_symbol,
                                                 balance)

select date('{start_date}') as period_date,
       'init_capital'     as protocol_id,
       position_id,
       wallet_address,
       pool_address,
       token_address,
       'deposit'          as deposit_borrow_type,
       token_symbol,
       deposit_balance    as balance
from deposit_table
where deposit_balance <> 0
union all
select date('{start_date}') as period_date,
       'init_capital'     as protocol_id,
       position_id,
       wallet_address,
       pool_address,
       token_address,
       'borrow'           as deposit_borrow_type,
       token_symbol,
       -borrow_balance    as balance
from borrow_table
where borrow_balance <> 0
;