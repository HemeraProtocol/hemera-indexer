delete
from period_feature_holding_balance_merchantmoe_cmeth
where period_date >= '{start_date}'
  and period_date < '{end_date}';
insert
into period_feature_holding_balance_merchantmoe_cmeth(period_date, protocol_id, contract_address, token_id,
                                                wallet_address, token0_address, token0_symbol, token0_balance,
                                                token1_address, token1_symbol, token1_balance)
with moe_pools_table as (select d0.*,

                                d4.symbol   as token0_symbol,
                                d4.decimals as token0_decimals,
                                d5.symbol   as token1_symbol,
                                d5.decimals as token1_decimals
                         from feature_merchant_moe_pools d0
                                  inner join tokens d4 on d0.token0_address = d4.address
                                  inner join tokens d5 on d0.token1_address = d5.address
                         where d4.symbol = 'cmETH'
                            or d5.symbol = 'cmETH'),

     moe_pool_with_records_table as (select d0.*, d1.address, d1.token_id, d1.balance
                                     from moe_pools_table d0
                                              inner join
                                          (select *
                                           from period_address_token_balances
                                           where token_type = 'ERC1155') d1
                                          on d0.token_address = d1.token_address),

     detail_table as (select d1.address
                           , d1.token_address
                           , d1.token_id
                           , d1.balance
                           , d2.total_supply
                           , d3.reserve0_bin
                           , d3.reserve1_bin
                           , token0_address
                           , token0_symbol
                           , token0_decimals
                           , token1_address
                           , token1_symbol
                           , token1_decimals
                      from moe_pool_with_records_table d1
                               inner join
                           (select *
                            from period_feature_erc1155_token_supply_records
                            where period_date = '{start_date}') d2
                           on d1.token_address = d2.token_address and d1.token_id = d2.token_id
                               inner join (select *
                                           from period_feature_merchant_moe_token_bin_records
                                           where period_date = '{start_date}') d3
                                          on d1.token_address = d3.token_address and d1.token_id = d3.token_id)

select date('{start_date}'),
       'merchantmoe'  as protocol_id,
       token_address  as nft_addres,
       token_id,
       address,
       token0_address,
       token0_symbol,
       case
           when total_supply > 0 then (balance / total_supply) * reserve0_bin / pow(10, token0_decimals)
           else 0 end as token0_balance,
       token1_address,
       token1_symbol,
       case
           when total_supply > 0 then (balance / total_supply) * reserve1_bin / pow(10, token1_decimals)
           else 0 end as token1_balance
from detail_table
;

