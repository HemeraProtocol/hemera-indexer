from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import text
from collections import namedtuple

from indexer.aggr_jobs.order_jobs.py_jobs.untils import get_engine

Q96 = 2 ** 96
root_c = 1.0001

address_mapping = {
    '0x218bf598d1453383e2f4aa7b14ffb9bfb102d637': 'agni',
    '0xaaa78e8c4241990b4ce159e105da08129345946a': 'cleoexchange',
    '0xc36442b4a4522e871399cd717abdd847ab11fe88': 'uniswap_v3',
    '0x5752f085206ab87d8a5ef6166779658add455774': 'fusionx',
    '0x46a15b0b27311cedf172ab29e4f4766fbe7f4364': 'pancake',
    '0x7d24de60a68ae47be4e852cf03dd4d8588b489ec': 'swapsicle'
}


def get_uniswap_v3_orms_from_new_mantle(start_date):
    # swapsicle
    Session = get_engine('MANTLE_POSTGRES_URL')
    session = Session()
    sql = f"""
select d1.period_date, d3.position_token_address as nft_address,d3.token_id,wallet_address, d1.pool_address as contract_address,liquidity, tick_upper, tick_lower, sqrt_price_x96, token0_address, token1_address,
                                         d5.decimals      AS token0_decimals,
                              d5.symbol        AS token0_symbol,
                              d6.decimals      AS token1_decimals,
                              d6.symbol        AS token1_symbol
    from af_uniswap_v3_pool_prices_period d1
         inner join af_uniswap_v3_pools d2
         on d1.pool_address = d2.pool_address
         inner join af_uniswap_v3_token_data_period d3 on d1.pool_address = d3.pool_address
         inner join af_uniswap_v3_tokens d4 ON d3.position_token_address = d4.position_token_address
                      AND d3.token_id = d4.token_id
                                            INNER JOIN tokens d5 ON d2.token0_address = d5.address
                                INNER JOIN tokens d6 ON d2.token1_address = d6.address

         where d1.period_date = '{start_date}' and d3.period_date = '{start_date}'
                                    and d5.symbol is not null and d6.symbol is not null
    """

    result = session.execute(text(sql))
    return result


def get_uniswap_v3_orms_from_old_mantle(db_service, start_date):
    session = db_service.Session()
    result = session.execute(text(f"""
        select d1.period_date, d3.nft_address,d3.token_id,wallet_address, d1.pool_address as contract_address,liquidity, tick_upper, tick_lower, sqrt_price_x96, token0_address, token1_address,
                                                 d5.decimals      AS token0_decimals,
                                      d5.symbol        AS token0_symbol,
                                      d6.decimals      AS token1_decimals,
                                      d6.symbol        AS token1_symbol
            from period_feature_uniswap_v3_pool_prices d1
                 inner join feature_uniswap_v3_pools d2
                 on d1.pool_address = d2.pool_address
                 inner join period_feature_uniswap_v3_token_details d3 on d1.pool_address = d3.pool_address
                 inner join feature_uniswap_v3_tokens d4 ON d3.nft_address = d4.nft_address
                              AND d3.token_id = d4.token_id
                                                    INNER JOIN tokens d5 ON d2.token0_address = d5.address
                                        INNER JOIN tokens d6 ON d2.token1_address = d6.address
            
                 where d1.period_date = '{start_date}' and d3.period_date = '{start_date}'
                                            and d5.symbol is not null and d6.symbol is not null
    
    """))
    session.close()
    return result


def get_detail_df(result):
    df = pd.DataFrame(result.fetchall(), columns=result.keys())

    for column in df.columns:
        if df[column].apply(lambda x: isinstance(x, memoryview)).any():
            df[column] = df[column].apply(lambda x: "0x" + x.tobytes().hex() if isinstance(x, memoryview) else x)
        elif df[column].apply(lambda x: isinstance(x, Decimal)).any():
            df[column] = df[column].astype(float)
    df['protocol_id'] = df['nft_address'].map(address_mapping).fillna('uniswap_v3')
    return df


def calculate_token_balance(df_):
    df_['sqrt_price'] = df_['sqrt_price_x96'] / Q96

    df_['sqrt_ratio_a'] = np.sqrt(root_c ** df_['tick_lower'])
    df_['sqrt_ratio_b'] = np.sqrt(root_c ** df_['tick_upper'])

    # condition1 = df_['sqrt_price_x96'] <= df_['tick_lower'] * Q96
    # condition2 = df_['sqrt_price_x96'] >= df_['tick_upper'] * Q96
    # condition3 = (df_['tick_lower'] * Q96 < df_['sqrt_price_x96']) & (df_['sqrt_price_x96'] < df_['tick_upper'] * Q96)

    df_['current_tick'] = np.log((df_['sqrt_price_x96'].astype(float) / float(Q96)) ** 2) / np.log(1.0001)
    condition1 = df_['current_tick'] <= df_['tick_lower']
    condition2 = df_['current_tick'] >= df_['tick_upper']
    condition3 = (df_['tick_lower'] < df_['current_tick']) & (df_['current_tick'] < df_['tick_upper'])

    df_['amount0_wei'] = 0
    df_['amount1_wei'] = 0

    df_.loc[condition1, 'amount0_wei'] = np.floor(
        df_['liquidity'] * (
                (df_['sqrt_ratio_b'] - df_['sqrt_ratio_a']) / (df_['sqrt_ratio_a'] * df_['sqrt_ratio_b'])))
    df_.loc[condition2, 'amount1_wei'] = np.floor(
        df_['liquidity'] * (df_['sqrt_ratio_b'] - df_['sqrt_ratio_a']))
    df_.loc[condition3, 'amount0_wei'] = np.floor(
        df_['liquidity'] * (
                (df_['sqrt_ratio_b'] - df_['sqrt_price']) / (df_['sqrt_price'] * df_['sqrt_ratio_b'])))
    df_.loc[condition3, 'amount1_wei'] = np.floor(df_['liquidity'] * (df_['sqrt_price'] - df_['sqrt_ratio_a']))

    df_['token0_balance'] = df_['amount0_wei'] / 10 ** df_['token0_decimals']
    df_['token1_balance'] = df_['amount1_wei'] / 10 ** df_['token1_decimals']


def rate_mapping(x):
    fbtc_pair_list = ['FBTC', 'WBTC']
    cmeth_pair_list = ['cmETH', 'WETH']
    cmeth_pair_list_ = ['cmETH', 'mETH']
    meth_pair_list = ['mETH', 'WETH']

    if x.token0_symbol in fbtc_pair_list and x.token1_symbol in fbtc_pair_list:
        return 0.01
    elif x.token0_symbol in cmeth_pair_list and x.token1_symbol in cmeth_pair_list:
        return 0.03
    elif x.token0_symbol in cmeth_pair_list_ and x.token1_symbol in cmeth_pair_list_:
        return 0.001
    elif x.token0_symbol in meth_pair_list and x.token1_symbol in meth_pair_list:
        return 0.03
    else:
        return 0.2


def calculate_liquidity(df, token_symbol):
    df['rate'] = df.apply(rate_mapping, axis=1)
    df['upper_rate'] = np.sqrt(1 + df['rate'])
    df['lower_rate'] = np.sqrt(1 - df['rate'])

    calculate_token_balance(df)

    df_balance_upper = df.copy()
    #  FBTC
    df_balance_upper.loc[df_balance_upper['token1_symbol'] == token_symbol, 'sqrt_price_x96'] = (
            df_balance_upper['sqrt_price_x96'] / df_balance_upper['upper_rate']
    )
    df_balance_upper.loc[df_balance_upper['token1_symbol'] != token_symbol, 'sqrt_price_x96'] = (
            df_balance_upper['sqrt_price_x96'] * df_balance_upper['upper_rate']
    )
    calculate_token_balance(df_balance_upper)

    df_balance_lower = df.copy()
    df_balance_lower.loc[df_balance_lower['token1_symbol'] == token_symbol, 'sqrt_price_x96'] = (
            df_balance_lower['sqrt_price_x96'] / df_balance_lower['lower_rate']
    )
    df_balance_lower.loc[df_balance_lower['token1_symbol'] != token_symbol, 'sqrt_price_x96'] = (
            df_balance_lower['sqrt_price_x96'] * df_balance_lower['lower_rate']
    )
    calculate_token_balance(df_balance_lower)

    df['token0_balance_upper'] = df_balance_upper['token0_balance']
    df['token1_balance_upper'] = df_balance_upper['token1_balance']

    df['token0_balance_lower'] = df_balance_lower['token0_balance']
    df['token1_balance_lower'] = df_balance_lower['token1_balance']

    # filter meet data
    filtered_df = df[
        ((df['token0_symbol'] == 'cmETH') | (df['token1_symbol'] == 'cmETH')
         # token0_symbol 或 token1_symbol 为 'cmETH'
         ) &
        ((df['token0_balance'] > 0) | (df['token1_balance'] > 0)  # token0_balance 或 token1_balance 大于 0
         )]
    return filtered_df


# FBTC OTHER
# upper -> decrease price; lower -> increase price
# OTHER FBTC
# upper -> increase price; lower -> decrease price
# grouped_df = df.groupby('contract_address').agg(
#     token0_balance_sum=('token0_balance', 'sum'),
#     token1_balance_sum=('token1_balance', 'sum')
# ).reset_index()
#
# # 按 token0_balance_sum 降序排序
# result_df = grouped_df.sort_values(by='token0_balance_sum', ascending=False)


def change_df_to_obj(df):
    for column in df.columns:
        if df[column].dtype == 'float64':
            df.loc[:, column] = df[column].apply(lambda x: Decimal(x) if not pd.isna(x) else x)

    Row = namedtuple('Row', df.columns)
    row_objects = [Row(*row) for row in df.itertuples(index=False, name=None)]
    return row_objects
