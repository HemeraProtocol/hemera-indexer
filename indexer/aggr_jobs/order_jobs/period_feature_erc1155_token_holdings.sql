begin;
delete
from period_feature_erc1155_token_holdings
WHERE period_date = '{start_date}';

insert into public.period_feature_erc1155_token_holdings(period_date, token_address, wallet_address, token_id, balance)
select date('{start_date}'),
       token_address,
       wallet_address,
       token_id,
       balance
from (select *,
             row_number() over (partition by wallet_address,token_id order by block_timestamp desc) as rn
      from feature_erc1155_token_holdings
      WHERE to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

commit