delete
from period_address_token_balances
where period_date = '{start_date}';
insert into period_address_token_balances(period_date, address, token_address, token_id, token_type, balance)
select date('{start_date}') as period_date, address, token_address, token_id, token_type, balance
from (select *, row_number() over (partition by address, token_address, token_id order by block_number desc) rn
      from address_token_balances) t
where rn = 1