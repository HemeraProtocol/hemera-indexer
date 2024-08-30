from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from sqlalchemy import text, func, desc, or_

from common.models.token_price import TokenPrice
from common.utils.format_utils import format_value_for_json
from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_fbtc_aggregates import PeriodFeatureDefiFbtcAggregates
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_fbtc_detail import PeriodFeatureDefiWalletFbtcDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_dodo import PeriodFeatureHoldingBalanceDoDo
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_lendle import PeriodFeatureHoldingBalanceLendle
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_merchantmoe import \
    PeriodFeatureHoldingBalanceMerchantmoe
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_staked_fbtc_detail import \
    PeriodFeatureHoldingBalanceStakedFbtcDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_uniswap_v3 import \
    PeriodFeatureHoldingBalanceUniswapV3

job_list = ['period_address_token_balances', 'period_feature_holding_balance_uniswap_v3.sql',
            'period_feature_holding_balance_staked_fbtc_detail.sql', 'period_feature_erc1155_token_holdings.sql',
            'period_feature_erc1155_token_supply_records.sql', 'period_feature_holding_balance_merchantmoe.sql',
            'period_feature_erc20_token_supply_records.sql', 'period_feature_holding_balance_dodo.sql',
            'period_feature_holding_balance_lendle.sql'
            ]


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]

    def run(self, **kwargs):
        start_date_limit = kwargs["start_date"]
        end_date_limit = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date_limit, end_date_limit)
        for date_pair in date_pairs:
            start_date, end_date = date_pair
            self.start_date = start_date

            for sql_name in job_list:
                sql_content = self.get_sql_content(sql_name, start_date, end_date)
                session.execute(text(sql_content))
                session.commit()

            self.results = []
            self.combine_json()
            self.insert_aggr_job(self.results)
        session.close()

    def get_pool_aggr(self, orm_list, price_dict):
        # 初始化一个字典用于分组
        grouped_data = defaultdict(list)

        # 按 period, wallet_address, protocol_id 分组
        for record in orm_list:
            key = (record.period_date, record.protocol_id)
            grouped_data[key].append(record)

        results = []

        for k, entity_list in grouped_data.items():
            period_date, protocol_id = k
            wallet_count = 0
            protocol_balance = 0
            protocol_usd = 0

            for entity in entity_list:
                token_usd0 = float(price_dict[entity.token0_symbol] * entity.token0_balance)
                token_usd1 = float(price_dict[entity.token1_symbol] * entity.token1_balance)

                wallet_count += 1

                if entity.token0_symbol == 'FBTC':
                    protocol_balance += float(entity.token0_balance)

                    protocol_usd += token_usd0
                if entity.token1_symbol == 'FBTC':
                    protocol_usd += token_usd1
                    protocol_balance += float(entity.token1_balance)

            results.append(
                PeriodFeatureDefiFbtcAggregates(
                    period_date=period_date,
                    chain_name='mantle',
                    protocol_id=protocol_id,
                    total_fbtc_balance=protocol_balance,
                    total_fbtc_usd=protocol_usd,
                    day_user_count=wallet_count,
                    total_user_count=wallet_count,
                    updated_version=1
                )

            )

        self.results.extend(results)

    def insert_aggr_job(self, results):
        session = self.db_service.Session()

        session.query(PeriodFeatureDefiFbtcAggregates).filter(
            PeriodFeatureDefiFbtcAggregates.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert successfully, {len(results)}')
        session.close()


    def get_pool_token_data(self, orm_list):
        distinct_symbol_list = []

        # 初始化一个字典用于分组
        grouped_data = defaultdict(list)

        # 按 period, wallet_address, protocol_id 分组
        for record in orm_list:
            key = (record.period_date, record.wallet_address, record.protocol_id)
            grouped_data[key].append(record)
            if record.token0_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token0_symbol)
            if record.token1_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token1_symbol)

        price_dict = self.get_latest_price(distinct_symbol_list)

        self.get_pool_aggr(orm_list, price_dict)

        results = {}
        for k, entity_list in grouped_data.items():
            period_date, wallet_address, protocol_id = k
            protocol_json = []
            token_json = []
            protocol_balance = 0
            protocol_usd = 0

            for entity in entity_list:
                token_usd0 = float(price_dict[entity.token0_symbol] * entity.token0_balance)
                token_usd1 = float(price_dict[entity.token1_symbol] * entity.token1_balance)
                j = {
                    "token_data": [
                        {
                            "token_symbol": entity.token0_symbol,
                            "token_address": format_value_for_json(entity.token0_address),
                            "token_balance": float(entity.token0_balance),
                            "token_balance_usd": token_usd0,
                        },
                        {
                            "token_symbol": entity.token1_symbol,
                            "token_address": format_value_for_json(entity.token1_address),
                            "token_balance": float(entity.token1_balance),
                            "token_balance_usd": token_usd1,
                        }
                    ],
                    "token_id": int(entity.token_id),
                    "contract_address": format_value_for_json(entity.contract_address),
                }
                token_json.append(j)
                if entity.token0_symbol == 'FBTC':
                    protocol_balance += float(entity.token0_balance)

                    protocol_usd += token_usd0
                if entity.token1_symbol == 'FBTC':
                    protocol_usd += token_usd1
                    protocol_balance += float(entity.token1_balance)

            h = {'pool_data': token_json,
                 'protocol_id': protocol_id}
            protocol_json.append(h)
            results[(period_date, wallet_address)] = {'contract_json': protocol_json, 'balance': protocol_balance,
                                                      'usd': protocol_usd}

        return results

    def get_latest_price(self, symbol_list):
        session = self.db_service.Session()

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
                TokenPrice.timestamp <= self.start_date)
            .filter(TokenPrice.symbol.in_(symbol_list))  # 应用过滤条件
            .subquery()
        )

        # 从子查询中选取 row_number 为 1 的记录
        latest_per_address = (
            session.query(subquery)
            .filter(subquery.c.row_number == 1)
            .all()
        )

        latest_per_address_dict = {tp.symbol: tp.price for tp in latest_per_address}
        session.close()
        return latest_per_address_dict

    def get_uniswap_v3_json(self):
        session = self.db_service.Session()
        uniswapV3_list = session.query(PeriodFeatureHoldingBalanceUniswapV3).filter(
            PeriodFeatureHoldingBalanceUniswapV3.period_date == self.start_date).filter(
            or_(
                PeriodFeatureHoldingBalanceUniswapV3.token0_symbol == 'FBTC',
                PeriodFeatureHoldingBalanceUniswapV3.token1_symbol == 'FBTC'
            )
        ).all()

        results = self.get_pool_token_data(uniswapV3_list)
        session.close()
        return results

    def get_token_aggr(self, orm_list, price_dict):
        grouped_data = defaultdict(list)
        for record in orm_list:
            key = (record.period_date, record.protocol_id)
            grouped_data[key].append(record)

        results = []
        for k, entity_list in grouped_data.items():
            period_date, protocol_id = k
            protocol_balance = 0
            protocol_usd = 0
            wallet_count = 0

            for entity in entity_list:
                fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
                token_usd = float(price_dict['FBTC'] * entity.balance) / 10 ** 8
                balance = float(entity.balance) / pow(10, 8)
                protocol_balance += balance
                protocol_usd += token_usd
                wallet_count += 1

            results.append(
                PeriodFeatureDefiFbtcAggregates(
                    period_date=period_date,
                    chain_name='mantle',
                    protocol_id=protocol_id,
                    total_fbtc_balance=protocol_balance,
                    total_fbtc_usd=protocol_usd,
                    day_user_count=wallet_count,
                    total_user_count=wallet_count,
                    updated_version=1
                )

            )

        self.results.extend(results)

    def get_staked_json(self):
        session = self.db_service.Session()

        fbtc_detail_list = session.query(PeriodFeatureHoldingBalanceStakedFbtcDetail).filter(
            PeriodFeatureHoldingBalanceStakedFbtcDetail.period_date == self.start_date).all()

        # 初始化一个字典用于分组
        grouped_data = defaultdict(list)

        # 按 period, wallet_address, protocol_id 分组
        for record in fbtc_detail_list:
            key = (record.period_date, record.wallet_address, record.protocol_id)
            grouped_data[key].append(record)

        price_dict = self.get_latest_price(['FBTC'])

        self.get_token_aggr(fbtc_detail_list, price_dict)

        results = {}
        for k, entity_list in grouped_data.items():
            period_date, wallet_address, protocol_id = k
            protocol_json = []
            token_json = []
            protocol_balance = 0
            protocol_usd = 0

            for entity in entity_list:
                fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
                token_usd = float(price_dict['FBTC'] * entity.balance) / 10 ** 8
                balance = float(entity.balance) / pow(10, 8)
                j = {
                    "token_data": [
                        {
                            "token_symbol": 'FBTC',
                            "token_address": fbtc_address,
                            "token_balance": balance,
                            "token_balance_usd": token_usd}
                    ],
                    "contract_address": format_value_for_json(entity.contract_address),
                }

                token_json.append(j)

                protocol_balance += balance
                protocol_usd += token_usd
            h = {'pool_data': token_json,
                 'protocol_id': protocol_id}
            protocol_json.append(h)
            results[(period_date, wallet_address)] = {'contract_json': protocol_json, 'balance': protocol_balance,
                                                      'usd': protocol_usd}
        session.close()
        return results

    def get_period_address_token_balances(self):
        fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
        address = bytes.fromhex(fbtc_address.lower()[2:])

        session = self.db_service.Session()
        # 创建窗口查询，并将其转换为子查询
        subquery = (
            session.query(
                PeriodAddressTokenBalances,
                func.row_number().over(
                    partition_by=PeriodAddressTokenBalances.address,  # 按 token_address 分区
                    order_by=desc(PeriodAddressTokenBalances.period_date)  # 按 period_date 倒序排序
                ).label('row_number')
            ).filter(
                PeriodAddressTokenBalances.period_date == self.start_date)
            .filter(PeriodAddressTokenBalances.token_address == address)  # 过滤条件
        ).subquery()

        # 在主查询中使用这个子查询，筛选出 row_number = 1 的记录
        query = session.query(subquery).filter(
            subquery.c.row_number == 1,
            subquery.c.balance > 0  # 添加 balance > 0 的过滤条件
        )

        # 执行查询并获取结果
        result = query.all()

        price_dict = self.get_latest_price(['FBTC'])

        # remember decimals
        return {
            (r.period_date, r.address): [float(r.balance / 10 ** 8), float(r.balance * price_dict['FBTC'] / 10 ** 8)]
            for r in result}

    def get_merchantmoe_json(self):
        session = self.db_service.Session()
        orm_list = session.query(PeriodFeatureHoldingBalanceMerchantmoe).filter(
            PeriodFeatureHoldingBalanceMerchantmoe.period_date == self.start_date).filter(
            or_(
                PeriodFeatureHoldingBalanceMerchantmoe.token0_symbol == 'FBTC',
                PeriodFeatureHoldingBalanceMerchantmoe.token1_symbol == 'FBTC'
            )
        ).all()

        results = self.get_pool_token_data(orm_list)
        session.close()
        return results

    def get_dodo_json(self):
        session = self.db_service.Session()
        orm_list = session.query(PeriodFeatureHoldingBalanceDoDo).filter(
            PeriodFeatureHoldingBalanceDoDo.period_date == self.start_date).filter(
            or_(
                PeriodFeatureHoldingBalanceDoDo.token0_symbol == 'FBTC',
                PeriodFeatureHoldingBalanceDoDo.token1_symbol == 'FBTC'
            )
        ).all()

        results = self.get_pool_token_data(orm_list)
        session.close()
        return results

    def get_lendle_json(self):
        session = self.db_service.Session()
        orm_list = session.query(PeriodFeatureHoldingBalanceLendle).filter(
            PeriodFeatureHoldingBalanceLendle.period_date == self.start_date).all()

        # 初始化一个字典用于分组
        grouped_data = defaultdict(list)

        # 按 period, wallet_address, protocol_id 分组
        for record in orm_list:
            key = (record.period_date, record.wallet_address, record.protocol_id)
            grouped_data[key].append(record)

        price_dict = self.get_latest_price(['FBTC'])

        self.get_token_aggr(orm_list, price_dict)

        results = {}
        for k, entity_list in grouped_data.items():
            period_date, wallet_address, protocol_id = k
            protocol_json = []
            token_json = []
            protocol_balance = 0
            protocol_usd = 0

            for entity in entity_list:
                fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
                token_usd = float(price_dict['FBTC'] * entity.balance)
                balance = float(entity.balance)
                j = {
                    "token_data": [
                        {
                            "token_symbol": 'FBTC',
                            "token_address": fbtc_address,
                            "token_balance": balance,
                            "token_balance_usd": token_usd}
                    ],
                    "contract_address": format_value_for_json(entity.contract_address),
                }

                token_json.append(j)

                protocol_balance += balance
                protocol_usd += token_usd
            h = {'pool_data': token_json,
                 'protocol_id': protocol_id}
            protocol_json.append(h)
            results[(period_date, wallet_address)] = {'contract_json': protocol_json, 'balance': protocol_balance,
                                                      'usd': protocol_usd}
        session.close()
        return results

    def combine_json(self):
        print(self.start_date)

        merchantmoe_json = self.get_merchantmoe_json()
        address_token_balances = self.get_period_address_token_balances()
        uniswapv3 = self.get_uniswap_v3_json()
        staked = self.get_staked_json()
        dodo_json = self.get_dodo_json()  # 无数据
        get_lendle_json = self.get_lendle_json()

        protocol_keys_list = list(uniswapv3.keys()) + list(staked.keys()) + list(address_token_balances.keys()) + list(
            merchantmoe_json.keys()) + list(dodo_json.keys()) + list(get_lendle_json.keys())

        keys_ = list(set(protocol_keys_list))
        result_orm_list = []

        for key in keys_:
            total_protocol_fbtc_balance = 0
            total_protocol_fbtc_usd = 0

            wallet_holding_fbtc_balance = 0
            wallet_holding_fbtc_usd = 0

            protocol_holding_detail = []

            address_token_balances_value = address_token_balances.get(key, '')
            if address_token_balances_value:
                wallet_holding_fbtc_balance += address_token_balances_value[0]
                wallet_holding_fbtc_usd += address_token_balances_value[1]

            uniswapv3_value = uniswapv3.get(key, '')
            if uniswapv3_value:
                protocol_holding_detail.extend(uniswapv3_value.get('contract_json'))
                total_protocol_fbtc_balance += uniswapv3_value.get('balance')
                total_protocol_fbtc_usd += uniswapv3_value.get('usd')

            staked_value = staked.get(key, '')
            if staked_value:
                protocol_holding_detail.extend(staked_value.get('contract_json'))
                total_protocol_fbtc_balance += staked_value.get('balance')
                total_protocol_fbtc_usd += staked_value.get('usd')

            merchantmoe_value = merchantmoe_json.get(key, '')
            if merchantmoe_value:
                protocol_holding_detail.extend(merchantmoe_value.get('contract_json'))
                total_protocol_fbtc_balance += merchantmoe_value.get('balance')
                total_protocol_fbtc_usd += merchantmoe_value.get('usd')

            dodo_json_value = dodo_json.get(key, '')
            if dodo_json_value:
                protocol_holding_detail.extend(dodo_json_value.get('contract_json'))
                total_protocol_fbtc_balance += dodo_json_value.get('balance')
                total_protocol_fbtc_usd += dodo_json_value.get('usd')

            lendle_json_value = get_lendle_json.get(key, '')
            if lendle_json_value:
                protocol_holding_detail.extend(lendle_json_value.get('contract_json'))
                total_protocol_fbtc_balance += lendle_json_value.get('balance')
                total_protocol_fbtc_usd += lendle_json_value.get('usd')

            period_date, wallet_address = key
            if protocol_holding_detail:
                print(format_value_for_json(wallet_address))
                print(protocol_holding_detail)
                pass

            record = PeriodFeatureDefiWalletFbtcDetail(
                period_date=period_date,
                wallet_address=format_value_for_json(wallet_address),
                chain_name='',
                contracts=protocol_holding_detail,
                total_protocol_fbtc_balance=total_protocol_fbtc_balance,
                total_protocol_fbtc_usd=total_protocol_fbtc_usd,
                wallet_holding_fbtc_balance=wallet_holding_fbtc_balance,
                updated_version=1,
                wallet_holding_fbtc_usd=wallet_holding_fbtc_usd,
                total_fbtc_balance=total_protocol_fbtc_balance + wallet_holding_fbtc_balance,
                total_fbtc_usd=total_protocol_fbtc_usd + wallet_holding_fbtc_usd,
                rank=0

            )
            result_orm_list.append(record)

        result_orm_list.sort(key=attrgetter('period_date', 'total_fbtc_balance'), reverse=True)

        grouped = groupby(result_orm_list, key=attrgetter('period_date'))

        for _, group in grouped:
            for idx, item in enumerate(group, start=1):
                item.rank = idx  # 模拟 SQL 中的 ROW_NUMBER

        session = self.db_service.Session()

        session.query(PeriodFeatureDefiWalletFbtcDetail).filter(
            PeriodFeatureDefiWalletFbtcDetail.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(result_orm_list)
        session.commit()
        session.close()
