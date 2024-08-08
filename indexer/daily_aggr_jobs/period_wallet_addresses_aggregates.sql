insert into period_wallet_addresses_aggregates
with interacted_address_table as (select d1.from_address            as address,
                                         count(distinct d2.address) as unique_address_interacted_count
                                  from transactions d1
                                           left join contracts d2
                                                     on d1.to_address = d2.address
                                                         and
                                                        d2.block_timestamp < '{today}'
                                  group by 1),

     today_table as (select *
                     from daily_wallet_addresses_aggregates
                     where block_date = '{yesterday}'),

     yesterday_table as (select *
                         from period_wallet_addresses_aggregates
                         where period_date = '{yesterday}'),

     s3 as (select coalesce(s1.address, s2.address)                      as address,
                   date('{today}')                                       as period_date,
                   COALESCE(s1.txn_count, 0) + COALESCE(s2.txn_count, 0) as txn_count,
                   COALESCE(s1.gas_used, 0) + COALESCE(s2.gas_used, 0)   as gas_used,
                   COALESCE(s1.contract_deployed_count, 0) +
                   COALESCE(s2.contract_deployed_count, 0)               as contract_deployed_count

            from today_table s1
                     full join yesterday_table s2 on
                s1.address = s2.address)

select s3.address,
       s3.period_date,
       s3.txn_count,
       s3.gas_used,
       s4.unique_address_interacted_count
from s3
         left join
     interacted_address_table s4
     on s3.address = s4.address
