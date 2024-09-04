delete
from period_address_token_balances
where period_date = '{start_date}';

with today_table as (select *
                     from daily_address_token_balances
                     where block_date = '{start_date}'),
     yesterday_table as (select *
                         from period_address_token_balances
                         where period_date = date('{start_date_previous}'))
insert
into public.period_address_token_balances (address, period_date, token_address, token_id, token_type, balance)

select coalesce(d1.address, d2.address)             as address,
       date('{start_date}')                         as period_date,
       coalesce(d1.token_address, d2.token_address) as token_address,
       coalesce(d1.token_id, d2.token_id)           as token_id,
       coalesce(d1.token_type, d2.token_type)       as token_type,
       coalesce(d1.balance, d2.balance)             as balance
from today_table d1
         full join yesterday_table d2
                   on d1.address = d2.address
                       and d1.token_address = d2.token_address;