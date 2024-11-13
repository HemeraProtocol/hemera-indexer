import configparser
import os
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


def get_engine():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 配置文件的相对路径
    config_file_path = os.path.join(current_dir, 'config.ini')

    config = configparser.ConfigParser()
    config.read(config_file_path)

    POSTGRES_URL = config['database']['POSTGRES_URL']

    engine = create_engine(POSTGRES_URL)

    Session = sessionmaker(bind=engine)
    return Session


def get_new_uniswap_v3_orms(period_date):
    # swapsicle
    Session = get_engine()
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
       token1_address,
       token1_symbol,
       token1_balance  from af_holding_balance_uniswap_v3_period
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
            wallet_address_json.append(protocol_json)

            results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                      'usd': total_usd}
    return results
