delete
from period_feature_holding_balance_lendle
where period_date >= '{start_date}'
  and period_date < '{end_date}';


with tokens_table as (select *,
                             CASE
                                 WHEN address = '\xdef3542bb1b2969c1966dd91ebc504f4b37462fe' THEN 1
                                 WHEN address = '\x874712c653aaaa7cfb201317f46e00238c2649bb' THEN -1
                                 WHEN address = '\x08fc23af290d538647aa2836c5b3cf2fb3313759' THEN -1
                                 ELSE 0
                                 END AS voucher_value
                      from tokens
                      where address in (
                                        '\xdef3542bb1b2969c1966dd91ebc504f4b37462fe',
                                        '\x874712c653aaaa7cfb201317f46e00238c2649bb',
                                        '\x08fc23af290d538647aa2836c5b3cf2fb3313759'
                          ))

insert
into period_feature_holding_balance_lendle (period_date, wallet_address, protocol_id, contract_address,
                                            token_symbol, token_address, balance)
select d1.period_date,
       d1.address,
       'lendle',
       d1.token_address,
       d3.symbol  as token_symbol,
       d3.address as token_address,
       d1.balance / pow(10, d2.decimals) * voucher_value

from period_address_token_balances d1
         inner join tokens_table d2 on d1.token_address = d2.address
         inner join tokens d3 on d3.symbol = 'FBTC'

where d1.period_date = '{start_date}'
  and token_address in (
                        '\xdef3542bb1b2969c1966dd91ebc504f4b37462fe',
                        '\x874712c653aaaa7cfb201317f46e00238c2649bb',
                        '\x08fc23af290d538647aa2836c5b3cf2fb3313759'
    );

