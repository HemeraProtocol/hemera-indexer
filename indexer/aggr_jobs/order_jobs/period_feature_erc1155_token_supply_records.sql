delete
from period_feature_erc1155_token_supply_records
WHERE period_date = '{start_date}';

insert into public.period_feature_erc1155_token_supply_records(period_date, token_address, token_id, total_supply)
select date('{start_date}'),
       token_address,
       token_id,
       total_supply
from (select *,
             row_number() over (partition by token_address, token_id order by block_date desc) as rn
      from daily_feature_erc1155_token_supply_records
      WHERE block_date < '{end_date}') t
where rn = 1;

