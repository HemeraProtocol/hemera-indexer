with detail_table as (select d1.wallet_address,
                             d1.token_address,
                             d1.token_id,
                             d1.balance,
                             d2.total_supply,
                             d3.reserve0_bin,
                             d3.reserve1_bin,
                             '\xc96de26018a54d51c097160568752c4e3bd6c364' as token0_address,
                             '\xcda86a272531e8640cd7f1a92c01839911b90bb0' as token1_address,
                             d4.symbol                                    as token0_symbol,
                             d4.decimals                                  as token0_decimals,
                             d5.symbol                                    as token1_symbol,
                             d5.decimals                                  as token1_decimals
                      from feature_erc1155_token_current_holdings d1
                               inner join
                           feature_erc1155_token_current_supply_status d2
                           on d1.token_address = d2.token_address and d1.token_id = d2.token_id
                               inner join feature_merchant_moe_token_bin_current_status d3
                                          on d1.token_address = d3.token_address and d1.token_id = d3.token_id
                               inner join tokens d4 on d4.address = '\xc96de26018a54d51c097160568752c4e3bd6c364'
                               inner join tokens d5 on d5.address = '\xcda86a272531e8640cd7f1a92c01839911b90bb0'

                      where wallet_address = '\x383DD7F649D692F7897D4DF06B781CD1E2E19293')


select sum(token0_amount), sum(token1_amount)
from (select wallet_address,
             token_address,
             token_id,
             token0_symbol,
             token1_symbol,
--        (balance / total_supply),
--        (balance / total_supply) * reserve0_bin,
--        (balance / total_supply) * reserve1_bin,
             (balance / total_supply) * reserve0_bin / pow(10, token0_decimals) as token0_amount,
             (balance / total_supply) * reserve1_bin / pow(10, token1_decimals) as token1_amount
      from detail_table) t