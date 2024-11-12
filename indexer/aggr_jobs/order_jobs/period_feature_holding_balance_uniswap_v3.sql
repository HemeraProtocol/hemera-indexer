delete
from af_uniswap_v3_token_data_period
where period_date >= '{start_date}'
  and period_date < '{end_date}';
insert into af_uniswap_v3_token_data_period(position_token_address, period_date, token_id, wallet_address, pool_address,
                                            liquidity)
select position_token_address,
       date('{start_date}')       as period_date,
       token_id,
       wallet_address,
       COALESCE(pool_address, '') as pool_address,
       liquidity
from (select *, row_number() over (partition by position_token_address, token_id order by block_number desc) rn
      from af_uniswap_v3_token_data_hist
      where to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

delete
from af_uniswap_v3_pool_prices_period
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert into af_uniswap_v3_pool_prices_period(pool_address, period_date, sqrt_price_x96)
select pool_address, date('{start_date}') as period_date, sqrt_price_x96
from (select *, row_number() over (partition by pool_address order by block_number desc) rn
      from af_uniswap_v3_pool_prices_hist
      where to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

delete
from af_holding_balance_uniswap_v3_period
where period_date >= '{start_date}'
  and period_date < '{end_date}';
with tokens_table as (select d1.address, d1.decimals, d1.symbol
                      from tokens d1
                      where d1.symbol is not null),
     detail_table as (SELECT d1.period_date,
                             d1.wallet_address,
                             d1.position_token_address,
                             d1.liquidity,
                             d1.pool_address,
                             d1.token_id,
                             d2.sqrt_price_x96,
                             d3.tick_lower,
                             d3.tick_upper,
                             d4.token0_address,
                             d4.token1_address,
                             d5.decimals                                                 as toekn0_decimals,
                             d5.symbol                                                   as token0_symbol,
                             d6.decimals                                                 as toekn1_decimals,
                             d6.symbol                                                   as token1_symbol,
                             sqrt(EXP(tick_lower * LN(1.0001)))                          as sqrt_ratio_a,
                             sqrt(EXP(tick_upper * LN(1.0001)))                          as sqrt_ratio_b,
                             FLOOR(LOG((sqrt_price_x96 / pow(2, 96)) ^ 2) / LOG(1.0001)) AS current_tick,
                             sqrt_price_x96 / pow(2, 96)                                 as sqrt_price

                      FROM (select * from af_uniswap_v3_token_data_period where period_date = '{start_date}') d1
                               inner join (select *
                                           from af_uniswap_v3_pool_prices_period
                                           where period_date = '{start_date}') d2 on
                          d1.pool_address = d2.pool_address
                               inner join af_uniswap_v3_tokens d3
                                          on d1.position_token_address = d3.position_token_address
                                              and d1.token_id = d3.token_id
                               inner join af_uniswap_v3_pools d4
                                          on d1.pool_address = d4.pool_address
                               inner join tokens_table d5
                                          on d4.token0_address = d5.address
                               inner join tokens_table d6
                                          on d4.token1_address = d6.address),
     tick_table as (select period_date,
                           wallet_address,
                           position_token_address,
                           pool_address,
                           token_id,
                           token0_address,
                           token0_symbol,
                           token1_symbol,
                           token1_address,
                           toekn0_decimals,
                           toekn1_decimals,
                           liquidity,
                           tick_lower,
                           tick_upper,
                           case
                               when current_tick <= tick_lower then
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
                               when current_tick > tick_lower and current_tick < tick_upper then
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)))
                               else 0
                               end / pow(10, toekn0_decimals)        AS token0_balance,
                           case
                               when current_tick >= tick_upper then floor(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
                               when current_tick > tick_lower and current_tick < tick_upper then
                                   floor(liquidity * (sqrt_price - sqrt_ratio_a))
                               else 0 end / pow(10, toekn1_decimals) AS token1_balance
                    from detail_table)
insert
into af_holding_balance_uniswap_v3_period(protocol_id,
                                          pool_address,
                                          period_date,
                                          token_id,
                                          wallet_address,
                                          token0_address,
                                          token0_symbol,
                                          token0_balance,
                                          token1_address,
                                          token1_symbol,
                                          token1_balance)
SELECT CASE
           WHEN position_token_address = '\x218bf598d1453383e2f4aa7b14ffb9bfb102d637' THEN 'agni'
           WHEN position_token_address = '\xaaa78e8c4241990b4ce159e105da08129345946a' THEN 'cleoexchange'
           WHEN position_token_address = '\xc36442b4a4522e871399cd717abdd847ab11fe88' THEN 'uniswap_v3'
           WHEN position_token_address = '\x5752f085206ab87d8a5ef6166779658add455774' then 'fusionx'
           WHEN position_token_address = '\x46a15b0b27311cedf172ab29e4f4766fbe7f4364' then 'pancake'
           WHEN position_token_address = '\x7d24de60a68ae47be4e852cf03dd4d8588b489ec' then 'swapsicle'
           ELSE 'uniswap_v3'
           END AS protocol_id,
       pool_address,
       period_date,
       token_id,
       wallet_address,
       token0_address,
       token0_symbol,
       token0_balance,
       token1_address,
       token1_symbol,
       token1_balance
from tick_table;