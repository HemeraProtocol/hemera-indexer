-- todo change to combine
begin;
delete
from period_address_token_balances
WHERE period_date < '{end_date}';

insert into public.period_address_token_balances (address, period_date, token_address, token_id, token_type, balance)
select address,
       '{start_date}',
       token_address,
       token_id,
       token_type,
       balance
from (select *,
             row_number() over (partition by address order by block_date desc) as rn
      from daily_address_token_balances
      WHERE block_date < '{end_date}') t
where rn = 1;

commit