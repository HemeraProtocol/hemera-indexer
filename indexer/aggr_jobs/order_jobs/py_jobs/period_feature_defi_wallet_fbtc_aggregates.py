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
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_init_capital import \
    PeriodFeatureHoldingBalanceInitCapital
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_lendle import PeriodFeatureHoldingBalanceLendle
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_merchantmoe import \
    PeriodFeatureHoldingBalanceMerchantmoe
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_staked_fbtc_detail import \
    PeriodFeatureHoldingBalanceStakedFbtcDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_uniswap_v3 import \
    PeriodFeatureHoldingBalanceUniswapV3
from indexer.aggr_jobs.order_jobs.py_jobs.PeriodFeatureDefiWalletAggregates import PeriodFeatureDefiWalletAggregates
from indexer.aggr_jobs.order_jobs.py_jobs.untils import get_latest_price, get_token_data_for_lendle_au_init_capital, \
    get_eigenlayer_orms, get_pool_token_pair_data, get_last_block_number_before_end_date


class PeriodFeatureDefiWalletFbtcAggregates(PeriodFeatureDefiWalletAggregates):
    def __init__(self, chain_name, db_service, start_date, end_date, version):
        super().__init__(chain_name, db_service, start_date, end_date, version)

        self.token_address = '0xc96de26018a54d51c097160568752c4e3bd6c364'
        self.token_symbol = 'FBTC'
        self.decimals = 10 ** 8
        price_dict = get_latest_price([self.token_symbol], self.db_service, self.end_date)
        self.price = price_dict.get(self.token_symbol, 0)
        pass

    def insert_aggr_job(self, results):
        session = self.db_service.Session()

        session.query(PeriodFeatureDefiFbtcAggregates).filter(
            PeriodFeatureDefiFbtcAggregates.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert successfully, {len(results)}')
        session.close()

    def get_pool_token_pair_data(self, orm_list):
        results = get_pool_token_pair_data(orm_list, self.token_symbol, self.db_service, self.end_date)
        self.get_pool_token_pair_aggr_by_protocol(orm_list, self.price)
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

    # def get_token_data(self, orm_list):
    #     self.get_token_aggr_by_protocol(orm_list, self.price)
    #     results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
    #                                                         self.end_date)
    #     results = self.get_token_data_old(orm_list)
    #
    #     return results

    def get_filter_start_date_orm(self, orm_class):
        session = self.db_service.Session()
        orm_list = session.query(orm_class).filter(
            orm_class.period_date == self.start_date).all()
        session.close()
        return orm_list

    def get_staked_json(self):
        orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceStakedFbtcDetail)
        # exclude init_capital
        filter_orm_list = []
        for orm in orm_list:
            if self.chain_name == 'mantle':
                if orm.protocol_id != 'init_capital':
                    filter_orm_list.append(orm)
            elif self.chain_name == 'bsc':
                if orm.protocol_id != 'satlayer':
                    filter_orm_list.append(orm)
            else:
                filter_orm_list.append(orm)
        results = self.get_token_data_old(filter_orm_list)

        return results

    def get_eigenlayer_json(self):
        orm_list = get_eigenlayer_orms(self.start_date)
        results = self.get_token_data_old(orm_list)
        return results

    def get_lendle_json(self):
        # all tokens
        orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceLendle)
        filter_orm_list = [r for r in orm_list if r.token_symbol == self.token_symbol]
        self.get_token_aggr_by_protocol(filter_orm_list, self.price)
        results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
                                                            self.end_date)
        return results

    def get_init_capital_json(self):
        # all tokens
        orm_list = self.get_filter_start_date_orm(PeriodFeatureHoldingBalanceInitCapital)
        filter_orm_list = [r for r in orm_list if r.token_symbol == self.token_symbol]
        self.get_token_aggr_by_protocol(filter_orm_list, self.price)
        results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
                                                            self.end_date)
        return results

    @staticmethod
    def timed_call(method, method_name):
        start_time = time.time()
        result = method()
        elapsed_time = time.time() - start_time
        print(f'took {elapsed_time:.2f} seconds by {method_name}')
        return result

    def run(self):
        # close
        last_block_number = get_last_block_number_before_end_date(self.db_service, self.end_date)

        init_capital = {}
        lendle_json = {}
        eigenlayer_json = {}

        if self.chain_name == 'mantle':
            init_capital = self.timed_call(self.get_init_capital_json, 'get_init_capital_json')
            lendle_json = self.timed_call(self.get_lendle_json, 'get_lendle_json')

        elif self.chain_name == 'eth':
            eigenlayer_json = self.get_eigenlayer_json()

        staked = self.timed_call(self.get_staked_json, 'get_staked_json')

        # get all protocol json, actually then can be abstract...
        address_token_balances = self.timed_call(self.get_period_address_token_balances,
                                                 'get_period_address_token_balances')

        uniswapv3 = self.timed_call(self.get_uniswap_v3_json, 'get_uniswap_v3_json')
        merchantmoe_json = self.timed_call(self.get_merchantmoe_json, 'get_merchantmoe_json')

        dodo_json = self.timed_call(self.get_dodo_json, 'get_dodo_json')

        # period_date can be removed from the key
        protocols = [uniswapv3, staked, merchantmoe_json, dodo_json, lendle_json, init_capital, eigenlayer_json]

        protocols_with_address_balance = protocols + [address_token_balances]

        protocol_wallet_keys_list = list({key for d in protocols_with_address_balance for key in d.keys()})

        result_orm_list = []

        for key in protocol_wallet_keys_list:
            total_protocol_fbtc_balance = 0
            total_protocol_fbtc_usd = 0

            wallet_holding_fbtc_balance = 0
            wallet_holding_fbtc_usd = 0

            protocol_holding_detail = []

            address_token_balances_value = address_token_balances.get(key)
            if address_token_balances_value:
                wallet_holding_fbtc_balance += address_token_balances_value[0]
                wallet_holding_fbtc_usd += address_token_balances_value[1]

            for protocol in protocols:
                protocol_value = protocol.get(key)
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
                rank=0,
                block_number=last_block_number,
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
