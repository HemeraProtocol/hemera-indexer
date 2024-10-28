delete
from period_feature_holding_balance_staked_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert
into period_feature_holding_balance_staked_fbtc_detail(period_date, wallet_address, protocol_id, contract_address, balance)
with sbtc_config as (select distinct contract_address, token_address
                     from feature_staked_fbtc_config),

     b_balance_table as (select d1.address,
                                d2.contract_address,
                                sum(d1.balance / pow(10, d3.decimals)) as b_balance
                         from period_address_token_balances d1
                                  inner join sbtc_config d2 on d1.token_address = d2.token_address
                                  left join tokens d3 on d2.token_address = d3.address
                         group by d1.address, d2.contract_address),


     c_balance_table as (select from_address,
                                d2.contract_address,
                                sum(value / pow(10, d3.decimals)) as c_balance
                         from erc20_token_transfers d1
                                  inner join feature_staked_fbtc_config d2
                                             on d1.token_address = d2.token_address and d1.to_address = d2.to_address
                                  left join tokens d3 on d2.token_address = d3.address
                         group by 1, 2),

     c_balance_protocol_table as (select from_address                      as wallet_address,
                                         d2.contract_address,
                                         d2.to_address_protocol_id         as protocol_id,
                                         d2.to_address,
                                         sum(value / pow(10, d3.decimals)) as balance
                                  from erc20_token_transfers d1
                                           inner join feature_staked_fbtc_config d2
                                                      on d1.token_address = d2.token_address and d1.to_address = d2.to_address
                                           left join tokens d3 on d2.token_address = d3.address
                                  group by 1, 2, 3, 4),


     a_balance_table as (select d1.wallet_address,
                                d1.contract_address,
                                d1.protocol_id,
                                d1.amount / pow(10, d2.decimals) as a_balance
                         from period_feature_staked_fbtc_detail_records d1
                                  inner join tokens d2 on d2.address = '\xC96DE26018A54D51C097160568752C4E3BD6C364'
                         where period_date = '{start_date}'),

     white_list_balance_table as (select d2.wallet_address,
                                         least(d1.a_balance, d2.balance) as balance,
                                         d2.protocol_id,
                                         d2.to_address                   as contract_address
                                  from a_balance_table d1
                                           inner join c_balance_protocol_table d2
                                                      on d1.wallet_address = d2.wallet_address
                                                          and d1.contract_address = d2.contract_address),


     original_staked_balance_table as (select d1.*,
                                              coalesce(d2.b_balance, 0)       as b_balance,
                                              coalesce(d3.c_balance, 0)       as c_balance,
                                              d4.contract_address is not null as if_config
                                       from a_balance_table d1
                                                left join b_balance_table d2 on
                                           d1.wallet_address = d2.address and d1.contract_address = d2.contract_address
                                                left join c_balance_table d3 on d1.wallet_address = d3.from_address
                                           and d1.contract_address = d3.contract_address
                                                left join (select distinct contract_address from feature_staked_fbtc_config) d4
                                                          on d1.contract_address = d4.contract_address)
        ,
     result_table as (select date('{start_date}')                as period_date,
                             d1.wallet_address,
                             d1.protocol_id,
                             d1.contract_address,
                             case
                                 when if_config then greatest(least(a_balance - c_balance, b_balance), 0)
                                 else greatest(a_balance, 0) end as balance
                      from original_staked_balance_table d1

                      union all
                      select date('{start_date}') as period_date,
                             wallet_address,
                             protocol_id,
                             contract_address,
                             balance
                      from white_list_balance_table)


select period_date, wallet_address, protocol_id, contract_address, balance
from result_table;