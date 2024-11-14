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
from af_holding_balance_uniswap_v3_period_cmeth
where period_date >= '{start_date}'
  and period_date < '{end_date}';
WITH pool_prices_table AS (SELECT d1.pool_address,
                                  sqrt_price_x96,
                                  case
                                      when (d5.symbol = 'cmETH' and d6.symbol = 'WETH') or
                                           (d6.symbol = 'cmETH' and d5.symbol = 'WETH')
                                          then 0.03
                                      else 0.2 end as rate_limit,

                                  d4.token0_address,
                                  d4.token1_address,
                                  d5.decimals      AS token0_decimals,
                                  d5.symbol        AS token0_symbol,
                                  d6.decimals      AS token1_decimals,
                                  d6.symbol        AS token1_symbol
                           FROM af_uniswap_v3_pool_prices_period d1
                                    INNER JOIN af_uniswap_v3_pools d4 ON d1.pool_address = d4.pool_address
                                    INNER JOIN tokens d5 ON d4.token0_address = d5.address
                                    INNER JOIN tokens d6 ON d4.token1_address = d6.address
                           WHERE period_date = '{start_date}'
                           and d5.symbol is not null and d6.symbol is not null
                           ),

     upper_lower_table as (select *,
                                  -- upperSqrtPrice
                                  CASE
                                      WHEN token1_address = '\xe6829d9a7ee3040e1276fa75293bde931859e8fa' THEN
                                          sqrt_price_x96 * (1 / POWER((1 + rate_limit), 0.5)) * 100000 / 100000 -- cmETH: sqrtPriceDividedChangeRate
                                      ELSE
                                          sqrt_price_x96 * POWER((1 + rate_limit), 0.5) * 100000 / 100000 --  token: sqrtPriceChangeRate
                                      END AS sqrt_price_x96_upper,

                                  -- lowerSqrtPrice
                                  CASE
                                      WHEN token1_address = '\xe6829d9a7ee3040e1276fa75293bde931859e8fa' THEN
                                          sqrt_price_x96 * (1 / POWER((1 - rate_limit), 0.5)) * 100000 / 100000 -- cmETH: sqrtPriceDividedChangeRate
                                      ELSE
                                          sqrt_price_x96 * POWER((1 - rate_limit), 0.5) * 100000 / 100000 --  token: sqrtPriceChangeRate
                                      END AS sqrt_price_x96_lower

                           from pool_prices_table),


     detail_table AS (SELECT d1.period_date,
                             d1.wallet_address,
                             d1.position_token_address,
                             d1.liquidity,
                             d1.pool_address,
                             d1.token_id,
                             d3.tick_lower,
                             d3.tick_upper,
                             token0_address,
                             token0_symbol,
                             token1_symbol,
                             token1_address,
                             token0_decimals,
                             token1_decimals,
                             sqrt(EXP(tick_lower * LN(1.0001)))                                AS sqrt_ratio_a,
                             sqrt(EXP(tick_upper * LN(1.0001)))                                AS sqrt_ratio_b,

                             -- Current tick for the original sqrt_price_x96
                             FLOOR(LOG((sqrt_price_x96 / pow(2, 96)) ^ 2) / LOG(1.0001))       AS current_tick,
                             sqrt_price_x96 / pow(2, 96)                                       AS sqrt_price,

                             -- Current tick for sqrt_price_x96_upper
                             FLOOR(LOG((sqrt_price_x96_upper / pow(2, 96)) ^ 2) / LOG(1.0001)) AS current_tick_upper,
                             sqrt_price_x96_upper / pow(2, 96)                                 AS sqrt_price_upper,

                             -- Current tick for sqrt_price_x96_lower
                             FLOOR(LOG((sqrt_price_x96_lower / pow(2, 96)) ^ 2) / LOG(1.0001)) AS current_tick_lower,
                             sqrt_price_x96_lower / pow(2, 96)                                 AS sqrt_price_lower

                      FROM af_uniswap_v3_token_data_period d1
                               INNER JOIN upper_lower_table d2 ON d1.pool_address = d2.pool_address
                               INNER JOIN af_uniswap_v3_tokens d3 ON d1.position_token_address = d3.position_token_address
                          AND d1.token_id = d3.token_id
                      WHERE d1.period_date = '{start_date}'),
     tick_table AS (SELECT period_date,
                           wallet_address,
                           position_token_address,
                           pool_address,
                           token_id,
                           token0_address,
                           token0_symbol,
                           token1_symbol,
                           token1_address,
                           token0_decimals,
                           token1_decimals,
                           liquidity,
                           tick_lower,
                           tick_upper,

                           -- Original token0_balance and token1_balance
                           CASE
                               WHEN current_tick <= tick_lower THEN
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
                               WHEN current_tick > tick_lower AND current_tick < tick_upper THEN
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)))
                               ELSE 0
                               END / pow(10, token0_decimals) AS token0_balance,
                           CASE
                               WHEN current_tick >= tick_upper THEN
                                   FLOOR(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
                               WHEN current_tick > tick_lower AND current_tick < tick_upper THEN
                                   FLOOR(liquidity * (sqrt_price - sqrt_ratio_a))
                               ELSE 0
                               END / pow(10, token1_decimals) AS token1_balance,

                           -- New token0_balance_upper and token1_balance_upper (using sqrt_price_x96_upper)
                           CASE
                               WHEN current_tick_upper <= tick_lower THEN
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
                               WHEN current_tick_upper > tick_lower AND current_tick_upper < tick_upper THEN
                                   FLOOR(liquidity *
                                         ((sqrt_ratio_b - sqrt_price_upper) / (sqrt_price_upper * sqrt_ratio_b)))
                               ELSE 0
                               END / pow(10, token0_decimals) AS token0_balance_upper,
                           CASE
                               WHEN current_tick_upper >= tick_upper THEN
                                   FLOOR(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
                               WHEN current_tick_upper > tick_lower AND current_tick_upper < tick_upper THEN
                                   FLOOR(liquidity * (sqrt_price_upper - sqrt_ratio_a))
                               ELSE 0
                               END / pow(10, token1_decimals) AS token1_balance_upper,

                           -- New token0_balance_lower and token1_balance_lower (using sqrt_price_x96_lower)
                           CASE
                               WHEN current_tick_lower <= tick_lower THEN
                                   FLOOR(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
                               WHEN current_tick_lower > tick_lower AND current_tick_lower < tick_upper THEN
                                   FLOOR(liquidity *
                                         ((sqrt_ratio_b - sqrt_price_lower) / (sqrt_price_lower * sqrt_ratio_b)))
                               ELSE 0
                               END / pow(10, token0_decimals) AS token0_balance_lower,
                           CASE
                               WHEN current_tick_lower >= tick_upper THEN
                                   FLOOR(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
                               WHEN current_tick_lower > tick_lower AND current_tick_lower < tick_upper THEN
                                   FLOOR(liquidity * (sqrt_price_lower - sqrt_ratio_a))
                               ELSE 0
                               END / pow(10, token1_decimals) AS token1_balance_lower

                    FROM detail_table)

insert
into af_holding_balance_uniswap_v3_period_cmeth(protocol_id,
                                                    pool_address,
                                                    period_date,
                                                    token_id,
                                                    wallet_address,
                                                    token0_address,
                                                    token0_symbol,
                                                    token0_balance,
                                                    token0_balance_upper,
                                                    token0_balance_lower,
                                                    token1_address,
                                                    token1_symbol,
                                                    token1_balance,
                                                    token1_balance_upper,
                                                    token1_balance_lower)


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
       token0_balance_upper,
       token0_balance_lower,
       token1_address,
       token1_symbol,
       token1_balance,
       token1_balance_upper,
       token1_balance_lower
FROM tick_table;