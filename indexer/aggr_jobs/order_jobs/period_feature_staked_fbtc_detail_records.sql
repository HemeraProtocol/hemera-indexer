begin;
delete
from period_feature_staked_fbtc_detail_records
where period_date >= '{start_date}'
  and period_date < '{end_date}';

with today_table as (select *
                     from daily_feature_staked_fbtc_detail_records
                     where block_date = '{start_date}'),
     yesterday_table as (select *
                         from period_feature_staked_fbtc_detail_records
                         where period_date = '{start_date_previous}')

insert
into period_feature_staked_fbtc_detail_records
select COALESCE(s1.contract_address, s2.contract_address) AS contract_address,
       COALESCE(s1.wallet_address, s2.wallet_address)     AS wallet_address,
       date('{start_date}')                               AS period_date,
--        COALESCE(s1.amount, 0) + COALESCE(s2.amount, 0)    AS amount, -- should not be plus
       COALESCE(s1.amount, s2.amount, 0)                  AS amount,
       COALESCE(s1.protocol_id, s2.protocol_id)           AS protocol_id
from today_table s1
         full join
     yesterday_table s2
     on s1.contract_address = s2.contract_address and s1.wallet_address = s2.wallet_address
         and s1.protocol_id = s2.protocol_id
;

delete
from period_feature_defi_wallet_fbtc_detail
where period_date >= '{start_date}'
  and period_date < '{end_date}';


insert into period_feature_defi_wallet_fbtc_detail
with period_token_price as (select symbol, price
                            from (select symbol,
                                         price,
                                         row_number() over (partition by symbol order by timestamp desc) rn
                                  from token_price
                                  where timestamp <= GREATEST('{start_date}', '2024-07-16')::date) t
                            where rn = 1),
     tokens_table as (select d1.address, d1.decimals, d1.symbol, d2.price
                      from tokens d1
                               left join
                           period_token_price d2 on d1.symbol = d2.symbol
                      where d1.symbol = 'FBTC'),

     period_balance as (select wallet_address, token_address, balance
                        from (select address as                                                             wallet_address,
                                     balance,
                                     token_address,
                                     row_number() over (partition by address order by block_timestamp desc) rn
                              from address_token_balances
                              where block_timestamp <= '{start_date}'
                                and token_address = '\xc96de26018a54d51c097160568752c4e3bd6c364') t
                        where rn = 1),
     wallet_holdings_table as (select d1.wallet_address,
                                      d1.balance / pow(10, d2.decimals)            as wallet_holding_fbtc_balance,
                                      d1.balance / pow(10, d2.decimals) * d2.price as wallet_holding_fbtc_usd
                               from period_balance d1
                                        inner join tokens_table d2
                                                   on d1.token_address = d2.address),
     protocol_table as (select d1.contract_address,
                               d1.wallet_address,
                               d2.symbol,
                               d2.address,
                               d1.protocol_id,
                               d1.amount / pow(10, d2.decimals)            as total_protocol_fbtc_balance,
                               d1.amount / pow(10, d2.decimals) * d2.price as total_protocol_fbtc_usd
                        from period_feature_staked_fbtc_detail_records d1,
                             tokens_table d2
                        where d1.period_date = '{start_date}'),

     total_balance_table as (select ''                                                                            as protocol_id,
                                    COALESCE(s1.wallet_address, s2.wallet_address)                                AS wallet_address,
                                    date('{start_date}')                                                          as period_date,
                                    'bsc'                                                                         as chain_name,

                                    COALESCE(wallet_holding_fbtc_balance, 0)                                      as wallet_holding_fbtc_balance,
                                    COALESCE(wallet_holding_fbtc_usd, 0)                                          as wallet_holding_fbtc_usd,
                                    COALESCE(total_protocol_fbtc_balance, 0)                                      as total_protocol_fbtc_balance,
                                    COALESCE(total_protocol_fbtc_usd, 0)                                          as total_protocol_fbtc_usd,


                                    COALESCE(s1.wallet_holding_fbtc_balance, 0) +
                                    COALESCE(s2.total_protocol_fbtc_balance, 0)                                   AS total_fbtc_balance,
                                    COALESCE(s1.wallet_holding_fbtc_usd, 0) +
                                    COALESCE(s2.total_protocol_fbtc_usd, 0)                                       AS total_fbtc_usd,
                                    DENSE_RANK() OVER (ORDER BY COALESCE(s1.wallet_holding_fbtc_balance, 0) +
                                                                COALESCE(s2.total_protocol_fbtc_balance, 0) DESC) AS rank
                             from wallet_holdings_table s1
                                      full join protocol_table s2
                                                on s1.wallet_address = s2.wallet_address),

     contracts_json as (SELECT jsonb_build_array(
                                       jsonb_build_object(
                                               'pool_data', jsonb_build_array(
                                               jsonb_build_object(
                                                       'token_data', jsonb_build_array(
                                                       jsonb_build_object(
                                                               'token_symbol', p.symbol,
                                                               'token_address', concat('0x', encode(p.address, 'hex')),
                                                               'token_balance', p.total_protocol_fbtc_balance,
                                                               'token_balance_usd', p.total_protocol_fbtc_usd
                                                       )
                                                                     ),
                                                       'contract_address', concat('0x', encode(contract_address, 'hex'))
                                               )
                                                            ),
                                               'protocol_id', p.protocol_id
                                       )
                               ) AS result_json,
                               wallet_address
                        FROM protocol_table p)


select s1.protocol_id,
       concat('0x', encode(s1.wallet_address, 'hex')) as wallet_address,
       s1.period_date,
       chain_name,
       s2.result_json                                 as contracts,
       s1.total_fbtc_balance,
       s1.total_fbtc_usd,
       s1.wallet_holding_fbtc_balance,
       s1.wallet_holding_fbtc_usd,
       1,
       s1.total_protocol_fbtc_balance,
       s1.total_protocol_fbtc_usd,
       s1.rank
from total_balance_table s1
         left join contracts_json s2
                   on s1.wallet_address = s2.wallet_address;


commit