import time
from collections import defaultdict
from datetime import datetime
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
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_satlayer_fbtc import \
    PeriodFeatureHoldingBalanceSatlayerFbtc
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_staked_fbtc_detail import \
    PeriodFeatureHoldingBalanceStakedFbtcDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_uniswap_v3 import \
    PeriodFeatureHoldingBalanceUniswapV3


class PeriodFeatureDefiWalletFbtcAggregates:
    def __init__(self, chain_name, db_service, start_date, end_date, version):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.end_date = end_date
        self.version = version
        self.results = []

    def insert_aggr_job(self, results):
        session = self.db_service.Session()

        session.query(PeriodFeatureDefiFbtcAggregates).filter(
            PeriodFeatureDefiFbtcAggregates.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert successfully, {len(results)}')
        session.close()

    def get_token_aggr_by_protocol(self, orm_list, price_dict):
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
                    updated_version=self.version
                )

            )

        self.results.extend(results)

    def get_pool_token_pair_aggr_by_protocol(self, orm_list, price_dict):
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
                    updated_version=self.version
                )

            )

        self.results.extend(results)

    def get_pool_token_pair_data(self, orm_list):
        distinct_symbol_list = []

        wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for record in orm_list:
            period_date_key = record.period_date
            wallet_key = record.wallet_address
            protocol_key = record.protocol_id
            contract_key = record.contract_address

            wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

            if record.token0_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token0_symbol)
            if record.token1_symbol not in distinct_symbol_list:
                distinct_symbol_list.append(record.token1_symbol)

        price_dict = self.get_latest_price(distinct_symbol_list)

        self.get_pool_token_pair_aggr_by_protocol(orm_list, price_dict)

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

        price_date_limit = max(self.end_date, '2024-07-12')

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

    def get_period_address_token_balances(self):
        fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
        address = bytes.fromhex(fbtc_address.lower()[2:])

        the_period_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()

        price_dict = self.get_latest_price(['FBTC'])
        results = {
            (the_period_date, r.address): [float(r.balance / 10 ** 8), float(r.balance * price_dict['FBTC'] / 10 ** 8)]
            for r in period_addresses}
        session.close()

        return results

    def get_uniswap_v3_json(self):
        uniswapV3_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceUniswapV3)
        results = self.get_pool_token_pair_data(uniswapV3_list)
        return results

    def get_merchantmoe_json(self):
        orm_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceMerchantmoe)
        results = self.get_pool_token_pair_data(orm_list)
        return results

    def get_dodo_json(self):
        orm_list = self.get_filter_fbtc_orm(PeriodFeatureHoldingBalanceDoDo)
        results = self.get_pool_token_pair_data(orm_list)
        return results

    def get_token_data_for_lendle_au(self, orm_list):
        fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'

        token_symbol_list = list({r.token_symbol for r in orm_list})

        price_dict = self.get_latest_price(token_symbol_list)

        wallet_protocol_contract_token_group = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

        for record in orm_list:
            period_date_key = record.period_date
            wallet_address = record.wallet_address
            protocol_id = record.protocol_id
            contract_address = format_value_for_json(record.contract_address)
            token_address = format_value_for_json(record.token_address)

            wallet_protocol_contract_token_group[(period_date_key, wallet_address)][protocol_id][contract_address][
                token_address].append(record)

        fbtc_orm_list = [r for r in orm_list if r.token_address.hex() == fbtc_address[2:]]
        self.get_token_aggr_by_protocol(fbtc_orm_list, price_dict)

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

                            if token_address == fbtc_address:
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

    def get_token_data(self, orm_list):
        price_dict = self.get_latest_price(['FBTC'])

        wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for record in orm_list:
            period_date_key = record.period_date
            wallet_key = record.wallet_address
            protocol_key = record.protocol_id
            contract_key = record.contract_address

            wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

        self.get_token_aggr_by_protocol(orm_list, price_dict)

        results = {}
        fbtc_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'

        for period_date_wallet, protocol_contract_group in wallet_protocol_contract_group.items():
            period_date, wallet_address = period_date_wallet

            wallet_address_json = []
            total_balance = 0
            total_usd = 0

            for protocol_id, contract_group in protocol_contract_group.items():
                protocol_json = {'pool_data': [],
                                 'protocol_id': protocol_id}
                for contract_address, records in contract_group.items():
                    contract_token_balance = 0
                    contract_token_usd = 0

                    for record in records:
                        token0_used = float(price_dict['FBTC'] * record.balance)

                        contract_token_balance += float(record.balance)
                        contract_token_usd += token0_used

                        total_balance += float(record.balance)
                        total_usd += token0_used

                    token_json = {
                        "token_data": [
                            {
                                "token_symbol": 'FBTC',
                                "token_address": fbtc_address,
                                "token_balance": contract_token_balance,
                                "token_balance_usd": contract_token_usd}
                        ],
                        "contract_address": format_value_for_json(record.contract_address),
                    }

                    protocol_json['pool_data'].append(token_json)
                wallet_address_json.append(protocol_json)

            results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
                                                      'usd': total_usd}
        return results

    def get_filter_start_date_orm(self, orm_class):
        session = self.db_service.Session()
        orm_list = session.query(orm_class).filter(
            orm_class.period_date == self.start_date).all()
        session.close()
        return orm_list

    def get_staked_json(self):
        orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceStakedFbtcDetail)
        return self.get_token_data(orm_list)

    # def get_satlayer_json(self):
    #     orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceSatlayerFbtc)
    #     return self.get_token_data(orm_list)

    def get_lendle_json(self):
        orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceLendle)
        results = self.get_token_data_for_lendle_au(orm_list)

        return results

    @staticmethod
    def timed_call(method, method_name):
        start_time = time.time()
        result = method()
        elapsed_time = time.time() - start_time
        print(f'took {elapsed_time:.2f} seconds by {method_name}')
        return result

    def run(self):

        lendle_json = self.timed_call(self.get_lendle_json, 'get_lendle_json')
        staked = self.timed_call(self.get_staked_json, 'get_staked_json')

        # get all protocol json, actually then can be abstract...
        address_token_balances = self.timed_call(self.get_period_address_token_balances,
                                                 'get_period_address_token_balances')

        uniswapv3 = self.timed_call(self.get_uniswap_v3_json, 'get_uniswap_v3_json')
        merchantmoe_json = self.timed_call(self.get_merchantmoe_json, 'get_merchantmoe_json')

        dodo_json = self.timed_call(self.get_dodo_json, 'get_dodo_json')

        # period_date can be removed from the key
        protocols = [uniswapv3, staked, merchantmoe_json, dodo_json, lendle_json]
        # if self.chain_name == 'eth':
        #     satlayer_json = self.timed_call(self.get_satlayer_json, 'get_satlayer_json')
        #     protocols.append(satlayer_json)

        protocols_with_address_balance = protocols + [address_token_balances]

        protocol_wallet_keys_list = list({key for d in protocols_with_address_balance for key in d.keys()})

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
                updated_version=self.version,
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
