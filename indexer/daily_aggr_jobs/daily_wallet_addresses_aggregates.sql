insert into daily_wallet_addresses_aggregates
with base_table as (select date(block_timestamp) as block_date,
                           hash,
                           from_address,
                           to_address,
                           gas * gas_price       as gas_used
                    from transactions
                    where block_timestamp >= '{yesterday}'
                      and block_timestamp < '{today}'),

     txn_table as (select block_date, address, count(1) as txn_count
                   from (select block_date, hash, from_address as address
                         from base_table
                         union
                         distinct
                         select block_date, hash, to_address as address
                         from base_table) as t
                   group by 1, 2),

     gas_used_table as (select block_date, from_address as address, sum(gas_used) as gas_used
                        from base_table
                        group by 1, 2),


     interacted_address_table as (select block_date,
                                         d1.from_address            as address,
                                         count(distinct d2.address) as unique_address_interacted_count
                                  from base_table d1
                                           left join contracts d2
                                                     on d1.to_address = d2.address
                                                         and d2.block_timestamp >= '{yesterday}' and
                                                        d2.block_timestamp < '{today}'
                                  group by 1, 2),

     contract_deployed_table as (select date(block_timestamp)    as block_date,
                                        transaction_from_address as address,
                                        count(1)                 as contract_deployed_count
                                 from contracts
                                 where block_timestamp >= '{yesterday}'
                                   and block_timestamp < '{today}'
                                 group by 1, 2)

select s1.block_date,
       s1.address,
       s1.txn_count,
       s2.gas_used,
       s3.unique_address_interacted_count,
       s4.contract_deployed_count
from txn_table s1
         left join gas_used_table s2 on s1.block_date = s2.block_date and s1.address = s2.address
         left join interacted_address_table s3 on s1.block_date = s3.block_date and s1.address = s3.address
         left join contract_deployed_table s4 on s1.block_date = s4.block_date and s1.address = s4.address
