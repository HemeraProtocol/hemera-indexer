begin;
delete
from period_feature_holding_balance_staked_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

with today_table as (select *
                     from daily_feature_holding_balance_staked_fbtc_detail
                     where block_date = '{start_date}'),
     yesterday_table as (select *
                         from daily_feature_holding_balance_staked_fbtc_detail
                         where period_date = '{start_date_previous}')

insert
into period_feature_holding_balance_staked_fbtc_detail
select COALESCE(s1.contract_address, s2.contract_address) AS contract_address,
       COALESCE(s1.wallet_address, s2.wallet_address)     AS wallet_address,
       date('{start_date}')                               AS period_date,
--        COALESCE(s1.amount, 0) + COALESCE(s2.amount, 0)    AS amount, -- should not be plus
       COALESCE(s1.amount, s2.amount, 0)                  AS amount,
       COALESCE(s1.protocol_id, s2.protocol_id)           AS protocol_id
from today_table s1
         full join
     yesterday_table s2
     on s1.contract_address = s2.contract_address and s1.wallet_address = s2.wallet_address
         and s1.protocol_id = s2.protocol_id
;

commit