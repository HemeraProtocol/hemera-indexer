-- delete from xxx;
select *
from (select *, row_number() over (partition by pool_address) rn
      from feature_uniswap_v3_pool_prices
      where called_block_timestamp >= 1720876007
        and called_block_timestamp < 1730886007) c
where rn = 1;


-- delete from xxx;
select *
from (select *, row_number() over (partition by nft_address, token_id) rn
      from feature_uniswap_v3_token_details
      where called_block_timestamp >= 1720876007
        and called_block_timestamp < 1730886007) t
where rn = 1;


