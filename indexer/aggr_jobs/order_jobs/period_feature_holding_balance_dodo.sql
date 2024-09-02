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

     address_balance as (select d1.address,
                                d1.token_address as token0_address,
                                d1.balance       as token0_balance,
                                d2.token_address as token1_address,
                                d2.balance       as token1_balance
                         from (select *
                               from period_address_token_balances
                               where period_date = '{start_date}'
                                 and address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'
                                 and token_address = '\xc96de26018a54d51c097160568752c4e3bd6c364') d1
                                  inner join
                              (select *
                               from period_address_token_balances
                               where period_date = '{start_date}'
                                 and address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'
                                 and token_address = '\xCAbAE6f6Ea1ecaB08Ad02fE02ce9A44F09aebfA2') d2
                              on d1.address = d2.address),


     fbtc_and_wbtc_balance_table as (select d1.address,
                                            d2.address                   as base_token_address,
                                            d2.symbol                    as base_token_symbol,
                                            d2.decimals                  as base_token_decimals,
                                            d3.address                   as quote_token_address,
                                            d3.symbol                    as quote_token_symbol,
                                            d3.decimals                  as quote_token_decimals,

                                            d1.token0_balance - 30373474 as base_balance,
                                            d1.token0_balance - 14587260 as quote_balance

                                     from address_balance d1
                                              inner join tokens d2 on d1.token0_address = d2.address
                                              inner join tokens d3 on d1.token0_address = d3.address)

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
       rate * base_balance / pow(10, base_token_decimals)      base_token_balance,
       d2.quote_token_address,
       d2.base_token_symbol,
       rate * quote_balance / pow(10, quote_token_decimals) as quote_token_balance

from gcb_balance d1
         inner join
     fbtc_and_wbtc_balance_table d2 on d1.token_address = d2.address
;





