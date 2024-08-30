begin;
delete
from period_feature_uniswap_v3_token_details
where period_date >= '{start_date}'
  and period_date < '{end_date}';

with today_table as (select *
                     from daily_feature_uniswap_v3_token_details
                     where block_date = '{start_date}'),
     yesterday_table as (select *
                         from period_feature_uniswap_v3_token_details
                         where period_date = '{start_date_previous}')

insert
into period_feature_uniswap_v3_token_details
select COALESCE(s1.nft_address, s2.nft_address)       AS nft_address,
       date('{start_date}')                           AS period_date,
       COALESCE(s1.token_id, s2.token_id)             AS token_id,
       COALESCE(s1.wallet_address, s2.wallet_address) AS wallet_address,
       COALESCE(s1.pool_address, s2.pool_address)     AS pool_address,
       COALESCE(s1.liquidity, s2.liquidity, 0)        AS liquidity
from today_table s1
         full join
     yesterday_table s2
     on s1.nft_address = s2.nft_address and s1.token_id = s2.token_id;

delete
from period_feature_uniswap_v3_pool_prices
where period_date >= '{start_date}'
  and period_date < '{end_date}';

with today_table as (select *
                     from daily_feature_uniswap_v3_pool_prices
                     where block_date = '{start_date}'),
     yesterday_table as (select *
                         from period_feature_uniswap_v3_pool_prices
                         where period_date = '{start_date_previous}')

insert
into period_feature_uniswap_v3_pool_prices
select COALESCE(s1.pool_address, s2.pool_address)        AS pool_address,
       date('{start_date}')                              AS period_date,
       COALESCE(s1.sqrt_price_x96, s2.sqrt_price_x96, 0) AS liquidity
from today_table s1
         full join
     yesterday_table s2
     on s1.pool_address = s2.pool_address;

delete
from period_feature_holding_balance_uniswap_v3
where period_date >= '{start_date}'
  and period_date < '{end_date}';
with period_token_price as (select symbol, price
                            from (select symbol,
                                         price,
                                         row_number() over (partition by symbol order by timestamp desc) rn
                                  from token_price
                                  where timestamp < '{end_date}') t
                            where rn = 1),
     tokens_table as (select d1.address, d1.decimals, d1.symbol, d2.price
                      from tokens d1
                               left join
                           period_token_price d2 on d1.symbol = d2.symbol
                      where d1.symbol is not null),
     detail_table as (SELECT d1.period_date,
                             d1.wallet_address,
                             d1.nft_address,
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
                             d5.price                                                    as token0_price,
                             d6.decimals                                                 as toekn1_decimals,
                             d6.symbol                                                   as token1_symbol,
                             d6.price                                                    as token1_price,
                             sqrt(EXP(tick_lower * LN(1.0001)))                          as sqrt_ratio_a,
                             sqrt(EXP(tick_upper * LN(1.0001)))                          as sqrt_ratio_b,
                             FLOOR(LOG((sqrt_price_x96 / pow(2, 96)) ^ 2) / LOG(1.0001)) AS current_tick,
                             sqrt_price_x96 / pow(2, 96)                                 as sqrt_price

                      FROM period_feature_uniswap_v3_token_details d1
                               inner join period_feature_uniswap_v3_pool_prices d2 on
                          d1.pool_address = d2.pool_address
                               inner join feature_uniswap_v3_tokens d3
                                          on d1.nft_address = d3.nft_address
                                              and d1.token_id = d3.token_id
                               inner join feature_uniswap_v3_pools d4
                                          on d1.pool_address = d4.pool_address
                               inner join tokens_table d5
                                          on d4.token0_address = d5.address
                               inner join tokens_table d6
                                          on d4.token1_address = d6.address
                      where d1.period_date = '{start_date}'
                        and d2.period_date = '{start_date}'),
     tick_table as (select period_date,
                           wallet_address,
                           nft_address,
                           token_id,
                           token0_address,
                           token0_symbol,
                           token1_symbol,
                           token1_address,
                           toekn0_decimals,
                           toekn1_decimals,
                           token0_price,
                           token1_price,
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
into period_feature_holding_balance_uniswap_v3(protocol_id,
                                               contract_address,
                                               period_date,
                                               token_id,
                                               wallet_address,
                                               token0_address,
                                               token0_symbol,
                                               token0_balance,
                                               token1_address,
                                               token1_symbol,
                                               token1_balance)
select case
           when nft_address = '\x218bf598d1453383e2f4aa7b14ffb9bfb102d637'
               then 'agni'
           when nft_address = '\xaaa78e8c4241990b4ce159e105da08129345946a' then 'cleoexchange'
           when nft_address = '\xc36442b4a4522e871399cd717abdd847ab11fe88' then 'uniswap_v3'
           else 'uniswap_v3' end as protoco_id,

       nft_address,
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

commit