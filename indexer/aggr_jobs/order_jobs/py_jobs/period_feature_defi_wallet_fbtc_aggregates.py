import time
from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from sqlalchemy import func, desc, or_, and_

from common.models.token_price import TokenPrice
from common.utils.format_utils import format_value_for_json
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


class PeriodFeatureDefiWalletFbtcAggregates:
    def __init__(self, chain_name, db_service, start_date):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.results = []

    def get_pool_aggr(self, orm_list, price_dict):
        grouped_data = defaultdict(list)

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
                token_usd0 = float(price_dict.get(entity.token0_symbol, 0) * entity.token0_balance)
                token_usd1 = float(price_dict.get(entity.token1_symbol, 0) * entity.token1_balance)

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
                    chain_name=self.chain_name,
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

        # 初始化三层字典
        wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for record in orm_list:
            period_date_key = record.period_date
            wallet_key = record.wallet_address
            protocol_key = record.protocol_id
            contract_key = record.contract_address
            # 使用 wallet_address 作为第一层的键，protocol_id 作为第二层的键，contract_address 作为第三层的键
            wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

            if record.token0_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token0_symbol)
            if record.token1_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token1_symbol)

        price_dict = self.get_latest_price(distinct_symbol_list)

        self.get_pool_aggr(orm_list, price_dict)

        results = {}
        for period_date_wallet, protocol_contract_group in wallet_protocol_contract_group.items():
            period_date, wallet_address = period_date_wallet
            # if wallet_address.hex() == '505d981b8d0df243f06f8a8b49d7d514dab98552':
            #     print(1)

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

                        if record.token0_symbol == 'FBTC':
                            total_balance += float(record.token0_balance)
                            total_usd += token_usd0

                        if record.token1_symbol == 'FBTC':
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
                        ], "contract_address": format_value_for_json(contract_address),
                    }

                    protocol_json['pool_data'].append(token_json)
                wallet_address_json.append(protocol_json)

            results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                      'usd': total_usd}
        return results

    def get_latest_price(self, symbol_list):
        session = self.db_service.Session()

        price_date_limit = max(self.start_date, '2024-07-12')

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
                TokenPrice.timestamp <= price_date_limit)
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

    def get_filter_fbtc_orm(self, orm_class):
        session = self.db_service.Session()
        orm_list = session.query(orm_class).filter(
            orm_class.period_date == self.start_date
        ).filter(
            or_(
                orm_class.token0_symbol == 'FBTC',
                orm_class.token1_symbol == 'FBTC'
            )
        ).filter(
            and_(
                or_(
                    orm_class.token0_balance > 0,
                    orm_class.token1_balance > 0
                )
            )
        ).all()
        session.close()
        return orm_list

    def get_uniswap_v3_json(self):
        uniswapV3_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceUniswapV3)
        results = self.get_pool_token_data(uniswapV3_list)

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
                token_usd = float(price_dict['FBTC'] * entity.balance)
                balance = float(entity.balance)
                protocol_balance += balance
                protocol_usd += token_usd
                wallet_count += 1

            results.append(
                PeriodFeatureDefiFbtcAggregates(
                    period_date=period_date,
                    chain_name=self.chain_name,
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

        grouped_data = defaultdict(list)

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

    def get_period_address_token_balances(self):
        fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
        address = bytes.fromhex(fbtc_address.lower()[2:])

        session = self.db_service.Session()
        subquery = (
            session.query(
                PeriodAddressTokenBalances,
                func.row_number().over(
                    partition_by=PeriodAddressTokenBalances.address,
                    order_by=desc(PeriodAddressTokenBalances.period_date)
                ).label('row_number')
            ).filter(
                PeriodAddressTokenBalances.period_date == self.start_date)
            .filter(PeriodAddressTokenBalances.token_address == address)
        ).subquery()

        query = session.query(subquery).filter(
            subquery.c.row_number == 1,
            subquery.c.balance > 0
        )

        result = query.all()

        price_dict = self.get_latest_price(['FBTC'])

        # remember decimals
        return {
            (r.period_date, r.address): [float(r.balance / 10 ** 8), float(r.balance * price_dict['FBTC'] / 10 ** 8)]
            for r in result}

    def get_merchantmoe_json(self):
        orm_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceMerchantmoe)
        results = self.get_pool_token_data(orm_list)
        return results

    def get_dodo_json(self):
        orm_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceDoDo)
        results = self.get_pool_token_data(orm_list)
        return results

    def get_lendle_json(self):
        session = self.db_service.Session()
        orm_list = session.query(PeriodFeatureHoldingBalanceLendle).filter(
            PeriodFeatureHoldingBalanceLendle.period_date == self.start_date).all()

        grouped_data = defaultdict(list)

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

    @staticmethod
    def timed_call(method, method_name):
        start_time = time.time()
        result = method()
        elapsed_time = time.time() - start_time
        print(f'took {elapsed_time:.2f} seconds by {method_name}')
        return result

    def run(self):
        # get all protocol json, actually then can be abstract...
        staked = self.timed_call(self.get_staked_json, 'get_staked_json')
        uniswapv3 = self.timed_call(self.get_uniswap_v3_json, 'get_uniswap_v3_json')
        merchantmoe_json = self.timed_call(self.get_merchantmoe_json, 'get_merchantmoe_json')
        address_token_balances = self.timed_call(self.get_period_address_token_balances,
                                                 'get_period_address_token_balances')

        dodo_json = self.timed_call(self.get_dodo_json, 'get_dodo_json')
        get_lendle_json = self.timed_call(self.get_lendle_json, 'get_lendle_json')

        protocol_wallet_keys_list = list(
            {key for d in [uniswapv3, staked, address_token_balances, merchantmoe_json, dodo_json, get_lendle_json] for
             key in d.keys()})

        result_orm_list = []

        for key in protocol_wallet_keys_list:
            total_protocol_fbtc_balance = 0
            total_protocol_fbtc_usd = 0

            wallet_holding_fbtc_balance = 0
            wallet_holding_fbtc_usd = 0

            protocol_holding_detail = []

            address_token_balances_value = address_token_balances.get(key, '')
            if address_token_balances_value:
                wallet_holding_fbtc_balance += address_token_balances_value[0]
                wallet_holding_fbtc_usd += address_token_balances_value[1]

            protocols = [uniswapv3, staked, merchantmoe_json, dodo_json, get_lendle_json]

            for protocol in protocols:
                protocol_value = protocol.get(key, '')
                if protocol_value:
                    protocol_holding_detail.extend(protocol_value.get('contract_json'))
                    total_protocol_fbtc_balance += protocol_value.get('balance')
                    total_protocol_fbtc_usd += protocol_value.get('usd')

            period_date, wallet_address = key

            record = PeriodFeatureDefiWalletFbtcDetail(
                period_date=period_date,
                wallet_address=format_value_for_json(wallet_address),
                chain_name=self.chain_name,
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
                item.rank = idx

        session = self.db_service.Session()

        session.query(PeriodFeatureDefiWalletFbtcDetail).filter(
            PeriodFeatureDefiWalletFbtcDetail.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(result_orm_list)
        session.commit()
        session.close()

        self.insert_aggr_job(self.results)