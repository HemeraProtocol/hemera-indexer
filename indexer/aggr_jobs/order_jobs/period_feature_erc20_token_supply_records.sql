delete
from period_feature_erc20_token_supply_records
WHERE period_date = '{start_date}';

insert into public.period_feature_erc20_token_supply_records(period_date, token_address, total_supply)
select date('{start_date}'),
       token_address,
       total_supply
from (select *,
             row_number() over (partition by token_address order by block_timestamp desc) as rn
      from feature_erc20_total_supply_records
      WHERE to_timestamp(block_timestamp) < '{end_date}') t
where rn = 1;

