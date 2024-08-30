begin;
delete
from daily_feature_erc1155_token_supply_records
WHERE block_date >= '{start_date}'
  and block_date < '{end_date}';

insert into public.daily_feature_erc1155_token_supply_records(block_date, token_address, token_id, total_supply)
select to_timestamp(block_timestamp)::date,
       token_address,
       token_id,
       total_supply
from (select *,
             row_number() over (partition by token_address, token_id order by block_timestamp desc) as rn
      from feature_erc1155_token_supply_records
      WHERE to_timestamp(block_timestamp) >= '{start_date}'
        and to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

commit