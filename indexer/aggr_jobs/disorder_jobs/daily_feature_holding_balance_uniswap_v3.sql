begin;
delete
from daily_feature_uniswap_v3_token_details
where block_date >= '{start_date}'
  and block_date < '{end_date}';
insert into daily_feature_uniswap_v3_token_details(nft_address, block_date,token_id, wallet_address, pool_address, liquidity)
select nft_address,
       TO_TIMESTAMP(block_timestamp)::DATE as block_date,
       token_id,
       wallet_address,
       COALESCE(pool_address, '')          as pool_address,
       liquidity
from (select *, row_number() over (partition by nft_address, token_id order by block_timestamp desc) rn
      from feature_uniswap_v3_token_details
      where TO_TIMESTAMP(block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(block_timestamp) < '{end_date}') t
where rn = 1;


delete
from daily_feature_uniswap_v3_pool_prices
where block_date >= '{start_date}'
  and block_date < '{end_date}';
insert into daily_feature_uniswap_v3_pool_prices(pool_address, block_date, sqrt_price_x96)
select pool_address,
       TO_TIMESTAMP(block_timestamp)::DATE as block_date,
       sqrt_price_x96
from (select *, row_number() over (partition by pool_address order by block_timestamp desc) rn
      from feature_uniswap_v3_pool_prices
      where TO_TIMESTAMP(block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(block_timestamp) < '{end_date}') t
where rn = 1;
commit