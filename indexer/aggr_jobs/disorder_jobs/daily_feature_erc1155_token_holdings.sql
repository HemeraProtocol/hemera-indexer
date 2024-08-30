begin;
delete
from daily_feature_erc1155_token_holdings
WHERE block_date >= '{start_date}'
  and block_date < '{end_date}';

insert into public.daily_feature_erc1155_token_holdings(block_date, token_address, wallet_address, token_id, balance)
select to_timestamp(block_timestamp)::date,
       token_address,
       wallet_address,
       token_id,
       balance
from (select *,
             row_number() over (partition by wallet_address order by block_timestamp desc) as rn
      from feature_erc1155_token_holdings
      WHERE to_timestamp(block_timestamp) >= '{start_date}'
        and to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

commit