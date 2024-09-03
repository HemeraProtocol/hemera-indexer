delete
from daily_feature_holding_balance_staked_fbtc_detail
where block_date >= '{start_date}'
  and block_date < '{end_date}';
insert into public.daily_feature_holding_balance_staked_fbtc_detail (block_date, wallet_address, protocol_id,
                                                                     contract_address, balance)
select TO_TIMESTAMP(block_timestamp)::DATE as block_date,
       wallet_address,
       protocol_id,
       contract_address,
       amount
from (select *,
             row_number()
             over (partition by contract_address, protocol_id, wallet_address order by block_timestamp desc) rn
      from feature_staked_fbtc_detail_records
      where TO_TIMESTAMP(block_timestamp) >= '{start_date}'
        and TO_TIMESTAMP(block_timestamp) < '{end_date}') t
where rn = 1;

