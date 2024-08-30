begin;
delete
from period_feature_holding_balance_dodo
where period_date >= '{start_date}'
  and period_date < '{end_date}';

WITH supply_cte AS (SELECT total_supply, 30373474 as base_fee, 14587260 as quote_fee
                    FROM period_feature_erc20_token_supply_records
                    WHERE period_date = '{start_date}'
                      and token_address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6' --gcb
),

     gcb_balance as (select period_date,
                            address,
                            token_address,
                            balance,
                            total_supply,
                            balance / total_supply as rate
                     from period_address_token_balances,
                          supply_cte
                     where period_date = '{start_date}'
                       and token_address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'),

     fbtc_and_wbtc_balance_table as (select d1.address,
                                            d2.address            as base_token_address,
                                            d2.symbol             as base_token_symbol,
                                            d2.decimals           as base_token_decimals,
                                            d3.address            as quote_token_address,
                                            d3.symbol             as quote_token_symbol,
                                            d3.decimals           as quote_token_decimals,
                                            d1.balance,
                                            d1.balance - 30373474 as base_balacne,
                                            d1.balance - 14587260 as quote_balance,
                                            d1.token_address,
                                            case
                                                when token_address = '\xc96de26018a54d51c097160568752c4e3bd6c364' then 1
                                                else 0 end        as token_flag

                                     from period_address_token_balances d1
                                              inner join tokens d2 on d2.address = '\xc96de26018a54d51c097160568752c4e3bd6c364'
                                              inner join tokens d3 on d3.address = '\x2260fac5e5542a773aa44fbcfedf7c193bc2c599'
                                     where period_date = '{start_date}'
                                       and d1.address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'
                                       and token_address in ('\xc96de26018a54d51c097160568752c4e3bd6c364',
                                                             '\x2260fac5e5542a773aa44fbcfedf7c193bc2c599'))
insert
into period_feature_holding_balance_dodo (period_date, protocol_id, contract_address, wallet_address, balance_of,
                                          total_supply, token0_address, token0_symbol, token0_balance,
                                          token1_address, token1_symbol, token1_balance)
select d1.period_date,
       'dodo',
       d1.token_address,
       d1.address,
       d1.balance,
       d1.total_supply,
       d2.base_token_address,
       d2.base_token_symbol,
       case
           when token_flag = 0 then rate * base_balacne / pow(10, base_token_decimals) end as base_token_balance,
       d2.quote_token_address,
       d2.base_token_symbol,
       case
           when token_flag = 1
               then rate * quote_balance / pow(10, quote_token_decimals) end               as quote_token_balance

from gcb_balance d1
         inner join
     fbtc_and_wbtc_balance_table d2 on d1.address = d2.address
;

commit
