


with detail_table as (SELECT d1.wallet_address,
                             d1.nft_address,
                             d1.liquidity,
                             d1.pool_address,
                             d1.token_id,
                             d2.sqrt_price_x96,
                             d3.tick_lower,
                             d3.tick_upper,
                             d4.token0_address,
                             d4.token1_address,
                             d5.decimals as toekn0_decimals,
                             d5.symbol   as token0_symbol,
                             d6.decimals as toekn1_decimals,
                             d6.symbol   as token1_symbol
                      FROM daily_feature_uniswap_v3_token_details d1
                               inner join daily_feature_uniswap_v3_pool_prices d2 on
                          d1.pool_address = d2.pool_address
                               inner join feature_uniswap_v3_tokens d3
                                          on d1.nft_address = d3.nft_address
                                              and d1.token_id = d3.token_id
                               inner join feature_uniswap_v3_pools d4
                                          on d1.pool_address = d4.pool_address
                               inner join tokens d5
                                          on d4.token0_address = d5.address
                               inner join tokens d6
                                          on d4.token1_address = d6.address),

     tick_table as (select wallet_address,
                           nft_address,
                           token_id,
                           token0_symbol,
                           token1_symbol,
                           toekn0_decimals,
                           toekn1_decimals,
                           liquidity,
                           tick_lower,
                           tick_upper,
                           sqrt(EXP(tick_lower * LN(1.0001)))                          as sqrt_ratio_a,
                           sqrt(EXP(tick_upper * LN(1.0001)))                          as sqrt_ratio_b,
                           FLOOR(LOG((sqrt_price_x96 / pow(2, 96)) ^ 2) / LOG(1.0001)) AS current_tick,
                           sqrt_price_x96 / pow(2, 96)                                 as sqrt_price
                    from detail_table)

select nft_address,
       token_id,
       token0_symbol,
       token1_symbol,
       case
           when current_tick <= tick_lower then
               FLOOR(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
           when current_tick > tick_lower and current_tick < tick_upper then
               FLOOR(liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)))
           else 0
           end / pow(10, toekn0_decimals)        AS amount0,
       case
           when current_tick >= tick_upper then floor(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
           when current_tick > tick_lower and current_tick < tick_upper then
               floor(liquidity * (sqrt_price - sqrt_ratio_a))
           else 0 end / pow(10, toekn1_decimals) AS amount1
from tick_table
