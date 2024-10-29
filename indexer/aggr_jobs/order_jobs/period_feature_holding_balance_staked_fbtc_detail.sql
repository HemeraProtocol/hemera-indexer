delete
from period_feature_holding_balance_staked_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert
into period_feature_holding_balance_staked_fbtc_detail(period_date, wallet_address, protocol_id, contract_address, balance)
with sbtc_config as (select distinct contract_address, token_address
                     from feature_staked_fbtc_config),

     sbtc_balance_table as (select d1.address,
                                   d2.contract_address,
                                   sum(d1.balance / pow(10, d3.decimals)) as sbtc_balance
                            from period_address_token_balances d1
                                     inner join sbtc_config d2 on d1.token_address = d2.token_address
                                     left join tokens d3 on d2.token_address = d3.address
                            group by d1.address, d2.contract_address),

     stbc_contract_balance_table as (select from_address,
                                            d2.contract_address,
                                            sum(value / pow(10, d3.decimals)) as btc_contract_balance
                                     from erc20_token_transfers d1
                                              inner join feature_staked_fbtc_config d2
                                                         on d1.token_address = d2.token_address and d1.to_address = d2.to_address
                                              left join tokens d3 on d2.token_address = d3.address
                                     group by 1, 2),

     start_date_staked_table as (select d1.wallet_address,
                                        d1.contract_address,
                                        d1.protocol_id,
                                        d1.amount / pow(10, d2.decimals) as fbtc_balance
                                 from period_feature_staked_fbtc_detail_records d1
                                          inner join tokens d2 on d2.address = '\xC96DE26018A54D51C097160568752C4E3BD6C364'
                                 where period_date = '{start_date}'),

     balance_table as (select d1.*,
                              coalesce(d2.sbtc_balance, 0) + coalesce(d3.btc_contract_balance, 0) as btc_banlance,
                              d2.sbtc_balance,
                              d3.btc_contract_balance,
                              d4.contract_address is not null                                     as if_config
                       from start_date_staked_table d1
                                left join sbtc_balance_table d2 on
                           d1.wallet_address = d2.address and d1.contract_address = d2.contract_address
                                left join stbc_contract_balance_table d3 on d1.wallet_address = d3.from_address
                           and d1.contract_address = d3.contract_address
                                left join (select distinct contract_address from feature_staked_fbtc_config) d4
                                          on d1.contract_address = d4.contract_address)


select date('{start_date}')                   as period_date,
       d1.wallet_address,
       d1.protocol_id,
       d1.contract_address,
       case
           when if_config then greatest(least(fbtc_balance, btc_banlance), 0)
           else greatest(fbtc_balance, 0) end as balance
from balance_table d1
order by fbtc_balance desc