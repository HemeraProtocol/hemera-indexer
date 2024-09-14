begin;
delete
from af_uniswap_v3_token_data_daily
where block_date >= '{start_date}'
  and block_date < '{end_date}';
insert into af_uniswap_v3_token_data_daily
select position_token_address,
       TO_TIMESTAMP(block_timestamp)::DATE as block_date,
       token_id,
       wallet_address,
       pool_address,
       liquidity
from (select *, row_number() over (partition by nft_address, token_id order by block_timestamp desc) rn
      from af_uniswap_v3_token_data_hist
      where TO_TIMESTAMP(block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(block_timestamp) < '{end_date}') t
where rn = 1;


delete
from af_uniswap_v3_pool_prices_daily
where block_date >= '{start_date}'
  and block_date < '{end_date}';
insert into af_uniswap_v3_pool_prices_daily
select pool_address,
       TO_TIMESTAMP(block_timestamp)::DATE as block_date,
       sqrt_price_x96
from (select *, row_number() over (partition by pool_address order by block_timestamp desc) rn
      from af_uniswap_v3_pool_prices_hist
      where TO_TIMESTAMP(block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(block_timestamp) < '{end_date}') t
where rn = 1;
commit