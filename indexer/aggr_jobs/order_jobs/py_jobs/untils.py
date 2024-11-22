import configparser
import math
import os
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, text, func, desc
from sqlalchemy.orm import sessionmaker

from common.models.token_price import TokenPrice


def format_value_for_json(value):
    if isinstance(value, memoryview):
        return "0x" + value.tobytes().hex()
    if isinstance(value, datetime):
        return value.astimezone().isoformat("T", "seconds")
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return "0x" + value.hex()
    else:
        return value


def get_block_number_sql(end_date):
    get_block_number_sql = f"""
    select number from blocks
                    WHERE  timestamp < '{end_date}'
    order by 1 desc limit 1;
    """
    return get_block_number_sql


def get_last_block_number_before_end_date_(chain_name, end_date):
    # temp solution because no blocks sync in the dev env
    if chain_name == 'eth':
        Session = get_engine('ETH_POSTGRES_URL')
    else:
        Session = get_engine('MANTLE_POSTGRES_URL')
    session = Session()
    sql = get_block_number_sql(end_date)
    result = session.execute(text(sql))
    row = result.fetchone()
    number = row.number
    if chain_name == 'bsc':
        number = None
    return number


def get_last_block_number_before_end_date(db_service, end_date):
    sql = f"""select block_number
from address_token_balances
where block_timestamp < '{end_date}'
  and block_timestamp > (date('{end_date}') - INTERVAL '1 day')
order by block_number desc
limit 1;
    """

    session = db_service.Session()
    result = session.execute(text(sql))
    row = result.fetchone()
    number = row.block_number
    return number


def get_engine(link_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    config_file_path = os.path.join(current_dir, 'config.ini')

    config = configparser.ConfigParser()
    config.read(config_file_path)

    POSTGRES_URL = config['database'][link_name]

    engine = create_engine(POSTGRES_URL)

    Session = sessionmaker(bind=engine)
    return Session


def get_eigenlayer_orms(period_date):
    Session = get_engine('ETH_POSTGRES_URL')
    session = Session()
    sql = f"""
    with filter_detail_table as (select d1.shares / pow(10, d2.decimals) as balance,
                                    d2.symbol,
                                    d1.staker                        as wallet_address,
                                    d1.token,
                                    d1.event_name,
                                    d1.withdrawroot
                             from af_eigen_layer_records d1
                                      inner join tokens d2 on d1.token = d2.address
                             where block_timestamp < '{period_date}'),

     deposit_detail_table as (select wallet_address, token, balance, symbol, withdrawroot
                              from filter_detail_table
                              where token = decode('c96de26018a54d51c097160568752c4e3bd6c364', 'hex')
                                and event_name = 'Deposit'),

     withdraw_detail_table as (select d2.wallet_address, d2.token, d1.balance
                               from filter_detail_table d1
                                        inner join deposit_detail_table d2 on d1.withdrawroot = d2.withdrawroot
                               where d1.event_name = 'WithdrawalCompleted'),

     deposit_balance_table as (select wallet_address, token, symbol, sum(balance) as blance
                               from deposit_detail_table
                               group by wallet_address, token, symbol),

     withdraw_balance_table as (select wallet_address, token, sum(balance) as blance
                                from withdraw_detail_table
                                group by wallet_address, token)
    select 
            date('{period_date}') as period_date,
            'eigenlayer' as protocol_id,
            s1.wallet_address,
           '0x858646372cc42e1a627fce94aa7a7033e7cf075a' as contract_address,
           s1.token as token_address,
           s1.symbol as token_symbol,
           s1.blance - coalesce(s2.blance, 0) as balance
    from deposit_balance_table s1
             left join withdraw_balance_table s2
                       on s1.wallet_address = s2.wallet_address and s1.token = s2.token
    """
    cursor = session.execute(text(sql))
    results = cursor.fetchall()
    return results


def get_new_uniswap_v3_orms(period_date):
    # swapsicle
    Session = get_engine('MANTLE_POSTGRES_URL')
    session = Session()
    sql = f"""
    select pool_address as contract_address,
        protocol_id,
       period_date,
       token_id,
       wallet_address,
       token0_address,
       token0_symbol,
       token0_balance,
       token0_balance_upper,
       token0_balance_lower,
       token1_address,
       token1_symbol,
       token1_balance,
       token1_balance_upper,
       token1_balance_lower  from af_holding_balance_uniswap_v3_period_cmeth
    where period_date = '{period_date}'
    and (token0_symbol = 'cmETH' or token1_symbol = 'cmETH') and (token0_balance> 0 or token1_balance > 0)
    """

    cursor = session.execute(text(sql))
    results = cursor.fetchall()
    return results


def get_filter_start_date_orm(orm_class, db_service, start_date):
    session = db_service.Session()
    orm_list = session.query(orm_class).filter(
        orm_class.period_date == start_date).all()
    session.close()
    return orm_list


def get_latest_price(symbol_list, db_service, end_date):
    session = db_service.Session()

    price_date_limit = max(end_date, '2024-07-12')
    subquery = (
        session.query(
            TokenPrice.symbol,
            TokenPrice.price,
            func.row_number().over(
                partition_by=TokenPrice.symbol,
                order_by=desc(TokenPrice.timestamp)
            ).label('row_number')
        )
        .filter(
            TokenPrice.timestamp < price_date_limit)
        .filter(TokenPrice.symbol.in_(symbol_list))
        .subquery()
    )

    latest_per_address = (
        session.query(subquery)
        .filter(subquery.c.row_number == 1)
        .all()
    )

    latest_per_address_dict = {tp.symbol: tp.price for tp in latest_per_address}
    session.close()
    return latest_per_address_dict


def get_token_data_for_lendle_au_init_capital(orm_list, target_token_address, db_service, end_date):
    token_symbol_list = list({r.token_symbol for r in orm_list})

    price_dict = get_latest_price(token_symbol_list, db_service, end_date)

    wallet_protocol_contract_token_group = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for record in orm_list:
        period_date_key = record.period_date
        wallet_address = format_value_for_json(record.wallet_address)
        protocol_id = record.protocol_id
        contract_address = format_value_for_json(record.contract_address)
        token_address = format_value_for_json(record.token_address)

        wallet_protocol_contract_token_group[(period_date_key, wallet_address)][protocol_id][contract_address][
            token_address].append(record)

    results = {}
    for period_date_wallet, protocol_contract_token_group in wallet_protocol_contract_token_group.items():
        period_date, wallet_address = period_date_wallet

        wallet_address_json = []
        total_balance = 0
        total_usd = 0

        for protocol_id, contract_token_group in protocol_contract_token_group.items():
            protocol_json = {'pool_data': [],
                             'protocol_id': protocol_id}

            for contract_address, token_group in contract_token_group.items():
                if target_token_address in token_group.keys():
                    token_data_list = []
                    for token_address, records in token_group.items():
                        token_group_balance = 0
                        token_group_usd = 0

                        for record in records:
                            symbol = format_value_for_json(record.token_symbol)
                            token0_used = float(price_dict.get(symbol, 0) * record.balance)

                            token_group_balance += float(record.balance)
                            token_group_usd += token0_used

                            if token_address == target_token_address:
                                total_balance += float(record.balance)
                                total_usd += token0_used

                        token_data_list.append({
                            "token_symbol": symbol,
                            "token_address": token_address,
                            "token_balance": token_group_balance,
                            "token_balance_usd": token_group_usd})

                    contract_json = {
                        "token_data": token_data_list,
                        "contract_address": contract_address,
                    }

                    protocol_json['pool_data'].append(contract_json)

            if protocol_json.get('pool_data'):
                wallet_address_json.append(protocol_json)

            results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                      'usd': total_usd}
    return results


def get_pool_token_pair_data(orm_list, target_token_symbol, db_service, end_date):
    distinct_symbol_list = []

    wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for record in orm_list:
        period_date_key = record.period_date
        wallet_key = format_value_for_json(record.wallet_address)
        protocol_key = record.protocol_id
        contract_key = format_value_for_json(record.contract_address)

        wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

        if record.token0_symbol not in distinct_symbol_list:
            distinct_symbol_list.append(record.token0_symbol)
        if record.token1_symbol not in distinct_symbol_list:
            distinct_symbol_list.append(record.token1_symbol)

    price_dict = get_latest_price(distinct_symbol_list, db_service, end_date)

    # self.get_pool_token_pair_aggr_by_protocol(orm_list, price_dict)

    results = {}
    for period_date_wallet, protocol_contract_group in wallet_protocol_contract_group.items():
        period_date, wallet_address = period_date_wallet

        wallet_address_json = []
        total_balance = 0
        total_usd = 0

        for protocol_id, contract_group in protocol_contract_group.items():
            protocol_json = {'pool_data': [],
                             'protocol_id': protocol_id}
            for contract_address, records in contract_group.items():
                contract_token0_balance = 0
                contract_token0_usd = 0

                contract_token1_balance = 0
                contract_token1_usd = 0

                for record in records:

                    token_usd0 = float(price_dict.get(record.token0_symbol, 0) * record.token0_balance)
                    token_usd1 = float(price_dict.get(record.token1_symbol, 0) * record.token1_balance)

                    if record.token0_symbol == target_token_symbol:
                        total_balance += float(record.token0_balance)
                        total_usd += token_usd0

                    if record.token1_symbol == target_token_symbol:
                        total_balance += float(record.token1_balance)
                        total_usd += token_usd1

                    contract_token0_balance += float(record.token0_balance)
                    contract_token0_usd += token_usd0

                    contract_token1_balance += float(record.token1_balance)
                    contract_token1_usd += token_usd1

                token_json = {
                    "token_data": [
                        {
                            "token_symbol": record.token0_symbol,
                            "token_address": format_value_for_json(record.token0_address),
                            "token_balance": contract_token0_balance,
                            "token_balance_usd": contract_token0_usd,
                        },
                        {
                            "token_symbol": record.token1_symbol,
                            "token_address": format_value_for_json(record.token1_address),
                            "token_balance": contract_token1_balance,
                            "token_balance_usd": contract_token1_usd,
                        }
                    ], "contract_address": contract_address,
                }

                protocol_json['pool_data'].append(token_json)
            wallet_address_json.append(protocol_json)

        results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                  'usd': total_usd}
    return results


# get token pair data with lp
def get_pool_token_pair_data_with_lp(orm_list, target_token_symbol, db_service, end_date, pool_type=''):
    distinct_symbol_list = []

    wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for record in orm_list:
        period_date_key = record.period_date
        wallet_key = format_value_for_json(record.wallet_address)
        protocol_key = record.protocol_id
        contract_key = format_value_for_json(record.contract_address)

        wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

        if record.token0_symbol not in distinct_symbol_list:
            distinct_symbol_list.append(record.token0_symbol)
        if record.token1_symbol not in distinct_symbol_list:
            distinct_symbol_list.append(record.token1_symbol)

    price_dict = get_latest_price(distinct_symbol_list, db_service, end_date)

    if pool_type == 'merchantmoe':
        merchant_moe_bin_step_active_id_records = get_merchant_moe_bin_step_active_id(db_service, end_date)

    results = {}
    for period_date_wallet, protocol_contract_group in wallet_protocol_contract_group.items():
        period_date, wallet_address = period_date_wallet

        wallet_address_json = []
        total_balance = 0
        total_usd = 0

        for protocol_id, contract_group in protocol_contract_group.items():
            protocol_json = {'pool_data': [],
                             'protocol_id': protocol_id}
            for contract_address, records in contract_group.items():

                token_pair_data = calculate_contract_token_balance(records, price_dict)

                if token_pair_data:
                    if token_pair_data[0].get('token_symbol') == target_token_symbol:
                        total_balance += token_pair_data[0].get('token_balance')
                        total_usd += token_pair_data[0].get('token_balance_usd')

                    if token_pair_data[1].get('token_symbol') == target_token_symbol:
                        total_balance += token_pair_data[1].get('token_balance')
                        total_usd += token_pair_data[1].get('token_balance_usd')

                token_json = {
                    'token_data': token_pair_data,
                    'contract_address': format_value_for_json(contract_address)}

                if pool_type == 'uniswapv3':
                    liquidity_data = concat_liquidity_token_data(records, price_dict)
                    token_json['liquidity_data'] = liquidity_data
                    pass
                elif pool_type == 'merchantmoe':
                    bin_step_active_id = merchant_moe_bin_step_active_id_records.get(contract_address)

                    range_within_records = calculate_merchant_moe_range_data(records, bin_step_active_id)
                    if range_within_records:
                        range_data = calculate_contract_token_balance(range_within_records, price_dict)
                    else:
                        range_data = []
                    token_json['range_data'] = range_data

                protocol_json['pool_data'].append(token_json)
            wallet_address_json.append(protocol_json)

        results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                  'usd': total_usd}
    return results


def bytes_to_hex_str(b: bytes) -> str:
    return "0x" + b.hex()


def get_merchant_moe_bin_step_active_id(db_service, end_date):
    session = db_service.Session()

    sql_query = """
            select pool_address, active_id, bin_step from (select *,
                                                          row_number()
                                                          over (partition by pool_address order by block_timestamp desc) as rn
                                                   from feature_merchant_moe_pool_records
                                                   where to_timestamp(block_timestamp) < :end_date) t where rn = 1        
            """

    result = session.execute(text(sql_query), {'end_date': end_date})

    rows = result.fetchall()
    results = {bytes_to_hex_str(row.pool_address): [row.bin_step, row.active_id] for row in rows}
    return results


def calculate_contract_token_balance(records, price_dict, balance_type='current'):
    contract_token0_balance = 0
    contract_token0_usd = 0

    contract_token1_balance = 0
    contract_token1_usd = 0

    for record in records:
        if balance_type == 'current':
            token0_balance = record.token0_balance
            token1_balance = record.token1_balance
        elif balance_type == 'upper':
            token0_balance = record.token0_balance_upper
            token1_balance = record.token1_balance_upper

        elif balance_type == 'lower':
            token0_balance = record.token0_balance_lower
            token1_balance = record.token1_balance_lower

        token_usd0 = float(price_dict.get(record.token0_symbol, 0) * token0_balance)
        token_usd1 = float(price_dict.get(record.token1_symbol, 0) * token1_balance)

        contract_token0_balance += float(token0_balance)
        contract_token0_usd += token_usd0

        contract_token1_balance += float(token1_balance)
        contract_token1_usd += token_usd1

    token_pair_data = [
        {
            "token_symbol": record.token0_symbol,
            "token_address": format_value_for_json(record.token0_address),
            "token_balance": contract_token0_balance,
            "token_balance_usd": contract_token0_usd,
        },
        {
            "token_symbol": record.token1_symbol,
            "token_address": format_value_for_json(record.token1_address),
            "token_balance": contract_token1_balance,
            "token_balance_usd": contract_token1_usd,
        }
    ]

    return token_pair_data


def calculate_merchant_moe_range_data(records, bin_step_active_id):
    if not bin_step_active_id:
        return []

    record = records[0]
    token0_symbol = record.token0_symbol
    token1_symbol = record.token1_symbol

    FBTC_CONDITION = (token0_symbol == 'FBTC' and token1_symbol == 'WBTC') or (
            token1_symbol == 'FBTC' and token0_symbol == 'WBTC')

    CMETH_CONDITION = (token0_symbol == 'cmETH' and token1_symbol == 'WETH') or (
            token1_symbol == 'cmETH' and token0_symbol == 'WETH')

    if FBTC_CONDITION or CMETH_CONDITION:
        rate = 0.03
    else:
        rate = 0.2

    upper_token_id = calculate_token_id(bin_step_active_id[0], bin_step_active_id[1], 1 + rate)
    lower_token_id = calculate_token_id(bin_step_active_id[0], bin_step_active_id[1], 1 - rate)

    results = [record for record in records if lower_token_id <= record.token_id <= upper_token_id]
    return results


def calculate_token_id(bin_step, active_id, rate):
    factor = 1 + (bin_step / 10000)
    token_id = active_id + math.log(rate) / math.log(factor)
    return token_id


def timed_call(method, method_name):
    start_time = time.time()
    result = method()
    elapsed_time = time.time() - start_time
    print(f'took {elapsed_time:.2f} seconds by {method_name}')
    return result


def get_token_data_dict(symbol, address, balance, price_dict):
    d = {
        "token_symbol": symbol,
        "token_address": address,
        "token_balance": format_value_for_json(balance),
        "token_balance_usd": format_value_for_json(balance * price_dict.get(symbol, 0)),
    }
    return d


def concat_liquidity_token_data(records, price_dict):
    liquidity_data_list = []
    for record in records:
        liquidity_data = {
            "token_id": record.token_id,
            "token_data": [
                get_token_data_dict(record.token0_symbol, record.token0_address, record.token0_balance, price_dict),
                get_token_data_dict(record.token1_symbol, record.token1_address, record.token1_balance, price_dict)],
            "token_data_lower": [
                get_token_data_dict(record.token0_symbol, record.token0_address, record.token0_balance_lower,
                                    price_dict),
                get_token_data_dict(record.token1_symbol, record.token1_address, record.token1_balance_lower,
                                    price_dict),
            ],
            "token_data_upper": [
                get_token_data_dict(record.token0_symbol, record.token0_address, record.token0_balance_upper,
                                    price_dict),
                get_token_data_dict(record.token1_symbol, record.token1_address, record.token1_balance_upper,
                                    price_dict)
            ]
        }
        liquidity_data_list.append(liquidity_data)
    return liquidity_data_list