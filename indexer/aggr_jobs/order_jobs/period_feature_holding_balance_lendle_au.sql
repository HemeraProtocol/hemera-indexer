delete
from period_feature_holding_balance_lendle_au
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert
into period_feature_holding_balance_lendle_au (period_date, wallet_address, protocol_id, contract_address,
                                               token_address, token_symbol, lb_debt_token_address, balance)
with lv_balance as (select d1.address                        as wallet_address,
                           'lendle'                          as protocol_id,
                           d2.pool_address,
                           d2.token_address,
                           d4.symbol,
                           d2.lv_address                     as lb_debt_token_address,
                           d1.balance / pow(10, d3.decimals) as balance
                    from period_address_token_balances d1
                             inner join lendle_token_mapping d2 on d1.token_address = d2.lv_address
                             inner join tokens d3 on d2.lv_address = d3.address
                             inner join tokens d4 on d2.token_address = d4.address
                    order by balance desc),

     debt_balance as (select d1.address                          as wallet_address,
                             'lendle'                            as protocol_id,
                             d2.pool_address,
                             d2.token_address,
                             d4.symbol,
                             d2.variable_debt_address            as lb_debt_token_address,
                             - d1.balance / pow(10, d3.decimals) as balance
                      from period_address_token_balances d1
                               inner join lendle_token_mapping d2 on d1.token_address = d2.variable_debt_address
                               inner join tokens d3 on d2.lv_address = d3.address
                               inner join tokens d4 on d2.token_address = d4.address
                      order by balance desc),


     au_lv_balance as (select d1.address                        as wallet_address,
                              'aurelius'                        as protocol_id,
                              d2.pool_address,
                              d2.token_address,
                              d4.symbol,
                              d2.lv_address                     as lb_debt_token_address,
                              d1.balance / pow(10, d3.decimals) as balance
                       from period_address_token_balances d1
                                inner join aurelius_token_mapping d2 on d1.token_address = d2.lv_address
                                inner join tokens d3 on d2.lv_address = d3.address
                                inner join tokens d4 on d2.token_address = d4.address
                       order by balance desc),

     au_debt_balance as (select d1.address                          as wallet_address,
                                'aurelius'                          as protocol_id,
                                d2.pool_address,
                                d2.token_address,
                                d4.symbol,
                                d2.variable_debt_address            as lb_debt_token_address,
                                - d1.balance / pow(10, d3.decimals) as balance
                         from period_address_token_balances d1
                                  inner join aurelius_token_mapping d2 on d1.token_address = d2.variable_debt_address
                                  inner join tokens d3 on d2.lv_address = d3.address
                                  inner join tokens d4 on d2.token_address = d4.address
                         order by balance desc)

select date('{start_date}') as period_date,
       wallet_address,
       protocol_id,
       pool_address,
       token_address,
       symbol,
       lb_debt_token_address,
       balance
from lv_balance
where balance > 0
union all

select date('{start_date}') as period_date,
       wallet_address,
       protocol_id,
       pool_address,
       token_address,
       symbol,
       lb_debt_token_address,
       balance
from debt_balance
where balance < 0
union all

select date('{start_date}') as period_date,
       wallet_address,
       protocol_id,
       pool_address,
       token_address,
       symbol,
       lb_debt_token_address,

       balance
from au_lv_balance
where balance > 0
union all

select date('{start_date}') as period_date,
       wallet_address,
       protocol_id,
       pool_address,
       token_address,
       symbol,
       lb_debt_token_address,
       balance
from au_debt_balance
where balance < 0