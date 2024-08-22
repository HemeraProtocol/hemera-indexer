-- delete from xxx;
select nft_address,
       token_id,
       TO_TIMESTAMP(called_block_timestamp)::DATE as block_date,
       wallet_address,
       pool_address,
       liquidity,
       create_time,
       update_time
from (select *, row_number() over (partition by nft_address, token_id) rn
      from feature_uniswap_v3_token_details
      where TO_TIMESTAMP(called_block_timestamp) >= '2024-08-01'
        and TO_TIMESTAMP(called_block_timestamp) < '2024-08-22') t
where rn = 1;


-- delete from xxx;
select pool_address,
       called_block_number,
       TO_TIMESTAMP(called_block_timestamp)::DATE as block_date,
       sqrt_price_x96,
       create_time,
       update_time
from (select *, row_number() over (partition by pool_address) rn
      from feature_uniswap_v3_pool_prices
      where TO_TIMESTAMP(called_block_timestamp) >= '2024-08-01'
        and TO_TIMESTAMP(called_block_timestamp) < '2024-08-22') t
where rn = 1


