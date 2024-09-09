delete
from period_feature_holding_balance_staked_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert
into period_feature_holding_balance_staked_fbtc_detail(period_date, wallet_address, protocol_id, contract_address, balance)
with sbtc_table as (select d1.*,
                           decode(substring(token_address, 3), 'hex')                    as token_address,
                           case when d2.protocol_id is not null then True else FALSE end as flag
                    from period_feature_staked_fbtc_detail_records d1
                             left join feature_staked_fbtc_lp_config d2 on d1.protocol_id = d2.protocol_id
                        and d1.contract_address = decode(substring(d2.contract_address, 3), 'hex')
                    where period_date = '{start_date}'),

     period_address_token_balance_table as (select *
                                            from period_address_token_balances),


     sbtc_balance_address_balance as (select d1.period_date,
                                             d1.wallet_address,
                                             d1.protocol_id,
                                             d1.contract_address,
                                             d1.amount  as fbtc_balance,
                                             d1.flag,
                                             d2.token_address,
                                             d2.balance as btc_balance
                                      from sbtc_table d1
                                               left join period_address_token_balance_table d2
                                                         on d1.wallet_address = d2.address
                                                             and d1.token_address = d2.token_address)

select date('{start_date}'),
       d1.wallet_address,
       d1.protocol_id,
       d1.contract_address,
       greatest(0, case
                       when not flag then d1.fbtc_balance / pow(10, d2.decimals)
                       else LEAST(d1.fbtc_balance / pow(10, d2.decimals), d1.btc_balance / pow(10, d3.decimals)) end)
           as balance

from sbtc_balance_address_balance d1
         left join tokens d2 on d2.address = '\xC96DE26018A54D51C097160568752C4E3BD6C364'
         left join tokens d3 on d1.token_address = d3.address
;