delete
from period_feature_holding_balance_staked_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert
into period_feature_holding_balance_staked_fbtc_detail(period_date, wallet_address, protocol_id, contract_address, balance)
with sbtc_config as (select decode(substring(contract_address, 3), 'hex') as contract_address,
                            decode(substring(token_address, 3), 'hex')    as token_address
                     from feature_staked_fbtc_lp_config),
     sbtc_balance_table as (select d1.address, d1.balance as sbtc_balance, d1.token_address, d2.contract_address
                            from period_address_token_balances d1
                                     inner join sbtc_config d2 on d1.token_address = d2.token_address),
     token_config as (select decode(substring('0xd6ab15b2458b6ec3e94ce210174d860fdbdd6b96', 3),
                                    'hex') as contract_address,
                             decode(substring('0xc75d7767f2edfbc6a5b18fc1fa5d51ffb57c2b37', 3),
                                    'hex') as token_address,
                             decode(substring('0xcf464ecc9a295edd53c1c3832fc41c2bc394a474', 3),
                                    'hex') as to_contrat_address
                      union
                      select decode(substring('0xf9775085d726e782e83585033b58606f7731ab18', 3),
                                    'hex') as contract_address,
                             decode(substring('0x93919784C523f39CACaa98Ee0a9d96c3F32b593e', 3),
                                    'hex') as token_address,
                             decode(substring('0x8f083eafcbba2e126ad9757639c3a1e25a061a08', 3),
                                    'hex') as to_contrat_address),
     stbc_contract_balance_table as (select from_address,
                                            d1.token_address,
                                            d2.contract_address,
                                            sum(value) as btc_contract_balance
                                     from erc20_token_transfers d1
                                              inner join token_config d2
                                                         on d1.token_address = d2.token_address and
                                                            d1.to_address = d2.to_contrat_address
                                     group by 1, 2, 3),
     start_date_staked_table as (select *
                                 from period_feature_staked_fbtc_detail_records
                                 where period_date = '{start_date}'),

     balance_table as (select d1.*,
                              coalesce(d2.token_address, d3.token_address)                        as sbtc_token_address,
                              coalesce(d2.sbtc_balance, 0) + coalesce(d3.btc_contract_balance, 0) as btc_banlance,
                              d2.sbtc_balance,
                              d3.btc_contract_balance

                       from start_date_staked_table d1
                                left join sbtc_balance_table d2 on
                           d1.wallet_address = d2.address and d1.contract_address = d2.contract_address
                                left join stbc_contract_balance_table d3 on d1.wallet_address = d3.from_address
                           and d1.contract_address = d3.contract_address)

select date('{start_date}'),
       d1.wallet_address,
       d1.protocol_id,
       d1.contract_address,
       greatest(0, least(d1.amount / pow(10, d2.decimals), d1.btc_banlance / pow(10, d3.decimals))) as balance
from balance_table d1
         left join tokens d2 on d2.address = '\xC96DE26018A54D51C097160568752C4E3BD6C364'
         left join tokens d3 on d1.sbtc_token_address = d3.address;
