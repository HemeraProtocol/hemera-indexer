delete
from period_feature_holding_balance_satlayer_fbtc
where period_date = '{start_date}';


insert into period_feature_holding_balance_satlayer_fbtc(period_date, wallet_address, protocol_id, contract_address, balance)
select date('{start_date}')               as period_date,
       d1.address                       as wallet_address,
       'satlayer'                       as protocol_id,
       token_address,
       balance / power(10, d2.decimals) as balance
from period_address_token_balances d1
         inner join tokens d2 on d1.token_address = d2.address
where token_address = '\xe2c6755c10d0b61d8b11dd2851ae8266cea912dc'
  and balance > 0
;