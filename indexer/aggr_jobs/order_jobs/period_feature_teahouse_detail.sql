delete
from period_feature_teahouse_detail
where period_date = '{start_date}';

with balance_table as (select *
                       from period_address_token_balances
                       where token_address in (decode('fc3861c04c5ce0883d9f79308e5a65402141df85', 'hex'),
                                               decode('4ddd37f662871fb49ebbc88a58897961e2c12a60', 'hex'))
                         and balance > 0),
     total_supply_table as (select *
                            from (select *, row_number() over (partition by token_address order by block_number desc) rn
                                  from af_erc20_total_supply_hist
                                  where token_address in (decode('fc3861c04c5ce0883d9f79308e5a65402141df85', 'hex'),
                                                          decode('4ddd37f662871fb49ebbc88a58897961e2c12a60', 'hex'))
                                    and to_timestamp(block_timestamp) < date('{start_date}') + interval '1 days') t
                            where rn = 1),

     user_share_table as (select d1.address                   as wallet_address,
                                 d1.token_address,
                                 d1.balance / d2.total_supply as share_percent
                          from balance_table d1
                                   inner join total_supply_table d2 on d1.token_address = d2.token_address),

     last_lp_table as (select *
                       from (select *, row_number() over (partition by pool_address order by block_number desc) rn
                             from af_teahouse_liquidity_hist
                             where to_timestamp(block_timestamp) < date('{start_date}') + interval '1 days') t
                       where rn = 1)

insert
into period_feature_teahouse_detail(period_date, position_token_address, wallet_address, share_percent, token_id,
                                    pool_address, liquidity, tick_upper, tick_lower, sqrt_price_x96, token0_address,
                                    token1_address, token0_decimals, token0_symbol, token1_decimals, token1_symbol)

select d1.period_date,
       d3.position_token_address,
       wallet_address,
       share_percent,
       null        as token_id,
       d1.pool_address,
       liquidity,
       tick_upper,
       tick_lower,
       sqrt_price_x96,
       token0_address,
       token1_address,
       d5.decimals AS token0_decimals,
       d5.symbol   AS token0_symbol,
       d6.decimals AS token1_decimals,
       d6.symbol   AS token1_symbol
from af_uniswap_v3_pool_prices_period d1
         inner join af_uniswap_v3_pools d2
                    on d1.pool_address = d2.pool_address
         inner join last_lp_table d3
                    on d1.pool_address = d3.pool_address
         inner join user_share_table d4 on d3.position_token_address = d4.token_address
         INNER JOIN tokens d5 ON d2.token0_address = d5.address
         INNER JOIN tokens d6 ON d2.token1_address = d6.address

where d1.period_date = '{start_date}'
  and d5.symbol is not null
  and d6.symbol is not null;