WITH supply_cte AS (SELECT total_supply, 30373474 as base_fee, 14587260 as quote_fee
                    FROM feature_erc20_current_total_supply_records
                    WHERE token_address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'
                    LIMIT 1),


     gcb_balance as (select address,
                            balance,
                            total_supply,
                            balance / total_supply as rate

                     from address_current_token_balances,
                          supply_cte
                     where address = '\x2d72307f1306f27bf0a8092b9bcc47dff03a3b97'
                       and token_address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'),

     fbtc_and_wbtc_balance_table as (select d1.address,
                                            d2.symbol             as base_token_symbol,
                                            d2.decimals           as base_token_decimals,
                                            d3.symbol             as quote_token_symbol,
                                            d3.decimals           as quote_token_decimals,
                                            d1.balance,
                                            d1.balance - 30373474 as base_balacne,
                                            d1.balance - 14587260 as quote_balance,
                                            d1.token_address,
                                            case
                                                when token_address = '\xc96de26018a54d51c097160568752c4e3bd6c364' then 1
                                                else 0 end        as token_flag

                                     from address_current_token_balances d1
                                              inner join tokens d2 on d2.address = '\xc96de26018a54d51c097160568752c4e3bd6c364'
                                              inner join tokens d3 on d3.address = '\x2260fac5e5542a773aa44fbcfedf7c193bc2c599'
                                     where d1.address = '\xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6'
                                       and token_address in ('\xc96de26018a54d51c097160568752c4e3bd6c364',
                                                             '\x2260fac5e5542a773aa44fbcfedf7c193bc2c599'))

select d1.address,
       rate,
       d1.balance,
       d1.total_supply,
       max(case
               when token_flag = 0 then rate * base_balacne / pow(10, base_token_decimals) end)   as base_token_balance,
       max(case
               when token_flag = 1 then rate * quote_balance / pow(10, quote_token_decimals) end) as quote_token_balance

from gcb_balance d1,
     fbtc_and_wbtc_balance_table d2
group by 1, 2, 3, 4
;
-- select * from fbtc_and_wbtc_balance_table




