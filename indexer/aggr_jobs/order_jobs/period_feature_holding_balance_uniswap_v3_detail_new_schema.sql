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


