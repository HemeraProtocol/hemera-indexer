begin;
delete
from period_feature_merchant_moe_token_bin_records
where period_date >= '{start_date}'
  and period_date < '{end_date}';

insert into period_feature_merchant_moe_token_bin_records(period_date, token_address, token_id, reserve0_bin, reserve1_bin)
select date('{start_date}'), token_address, token_id, reserve0_bin, reserve1_bin
from (select *, row_number() over (partition by token_address, token_id order by block_timestamp desc) as rn
      from feature_merchant_moe_token_bin_records
      where to_timestamp(block_timestamp) <= '{start_date}') t
where rn = 1
;


delete
from period_feature_holding_balance_merchantmoe
where period_date >= '{start_date}'
  and period_date < '{end_date}';
with detail_table as (select d1.wallet_address,
                             d1.token_address,
                             d1.token_id,
                             d1.balance,
                             d2.total_supply,
                             d3.reserve0_bin,
                             d3.reserve1_bin,
--                              concat('0x', encode(d4.address, 'hex')) as token0_address,
--                              concat('0x', encode(d5.address, 'hex')) as token1_address,
                             d4.address  as token0_address,
                             d5.address  as token1_address,

                             d4.symbol   as token0_symbol,
                             d4.decimals as token0_decimals,
                             d5.symbol   as token1_symbol,
                             d5.decimals as token1_decimals
                      from feature_merchant_moe_pools d0
                               inner join
                           period_feature_erc1155_token_holdings d1 on d0.token_address = d1.token_address
                               inner join
                           period_feature_erc1155_token_supply_records d2
                           on d1.token_address = d2.token_address and d1.token_id = d2.token_id
                               inner join period_feature_merchant_moe_token_bin_records d3
                                          on d1.token_address = d3.token_address and d1.token_id = d3.token_id
                               inner join tokens d4 on d0.token0_address = d4.address
                               inner join tokens d5 on d0.token1_address = d5.address
                      where d1.period_date = '{start_date}'
                        and d2.period_date = '{start_date}'
                        and d3.period_date = '{start_date}')


insert
into period_feature_holding_balance_merchantmoe(period_date, protocol_id, contract_address, token_id,
                                                wallet_address, token0_address, token0_symbol, token0_balance,
                                                token1_address, token1_symbol, token1_balance)

select date('{start_date}'),
       'merchantmoe'                                                      as protocol_id,
       token_address                                                      as nft_addres,
       token_id,
       wallet_address,
       token0_address,
       token0_symbol,
       (balance / total_supply) * reserve0_bin / pow(10, token0_decimals) as token0_balance,
       token1_address,
       token1_symbol,
       (balance / total_supply) * reserve1_bin / pow(10, token1_decimals) as token1_amount
from detail_table
where token0_symbol = 'FBTC'
   or token1_symbol = 'FBTC'
;

commit
