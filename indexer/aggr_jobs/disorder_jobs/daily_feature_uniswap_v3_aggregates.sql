begin;
delete
from daily_feature_uniswap_v3_token_details
where block_date >= '{start_date}'
  and block_date < '{start_date}';
insert into daily_feature_uniswap_v3_token_details
select nft_address,
       TO_TIMESTAMP(called_block_timestamp)::DATE as block_date,
       token_id,
       wallet_address,
       pool_address,
       liquidity
from (select *, row_number() over (partition by nft_address, token_id) rn
      from feature_uniswap_v3_token_details
      where TO_TIMESTAMP(called_block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(called_block_timestamp) < '{start_date}') t
where rn = 1;


delete
from daily_feature_uniswap_v3_pool_prices
where block_date >= '{start_date}'
  and block_date < '{start_date}';
insert into daily_feature_uniswap_v3_pool_prices
select pool_address,
       TO_TIMESTAMP(called_block_timestamp)::DATE as block_date,
       sqrt_price_x96
from (select *, row_number() over (partition by pool_address) rn
      from feature_uniswap_v3_pool_prices
      where TO_TIMESTAMP(called_block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(called_block_timestamp) < '{start_date}') t
where rn = 1;
commit