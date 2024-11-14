import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from itertools import groupby
from operator import attrgetter

from sqlalchemy import func, desc, or_, and_, text

from common.models.token_price import TokenPrice
from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_cmeth_aggregates import PeriodFeatureDefiCmethAggregates
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_cmeth_detail import \
    PeriodFeatureDefiWalletCmethDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_init_capital import \
    PeriodFeatureHoldingBalanceInitCapital
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_lendle import PeriodFeatureHoldingBalanceLendle
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_merchantmoe_cmeth import \
    PeriodFeatureHoldingBalanceMerchantmoeCmeth
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_uniswap_v3 import \
    PeriodFeatureHoldingBalanceUniswapV3, PeriodFeatureHoldingBalanceUniswapV3Cmeth
from indexer.aggr_jobs.order_jobs.py_jobs.untils import format_value_for_json, get_new_uniswap_v3_orms, \
    get_latest_price, get_token_data_for_lendle_au_init_capital, get_filter_start_date_orm, get_pool_token_pair_data, \
    get_pool_token_pair_data_with_lp, timed_call


class PeriodFeatureDefiWalletCmethAggregates:
    def __init__(self, chain_name, db_service, start_date, end_date, version):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.end_date = end_date
        self.version = version
        self.results = []

        self.token_address = '0xe6829d9a7ee3040e1276fa75293bde931859e8fa'
        self.token_symbol = 'cmETH'
        price_dict = get_latest_price([self.token_symbol], self.db_service, self.end_date)
        self.price = price_dict.get(self.token_symbol, 0)
        # self._new_session = get_engine()

    def insert_aggr_job(self, results):
        session = self.db_service.Session()

        session.query(PeriodFeatureDefiCmethAggregates).filter(
            PeriodFeatureDefiCmethAggregates.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert cmeth successfully, {len(results)}')
        session.close()

    def get_pool_token_pair_aggr_by_protocol(self, orm_list, price):
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
                wallet_count += 1
                if entity.token0_symbol == self.token_symbol:
                    token_usd0 = float(price * entity.token0_balance)
                    protocol_balance += float(entity.token0_balance)
                    protocol_usd += token_usd0
                if entity.token1_symbol == self.token_symbol:
                    token_usd1 = float(price * entity.token1_balance)
                    protocol_balance += float(entity.token1_balance)
                    protocol_usd += token_usd1

            results.append(
                PeriodFeatureDefiCmethAggregates(
                    period_date=period_date,
                    chain_name=self.chain_name,
                    protocol_id=protocol_id,
                    total_cmeth_balance=protocol_balance,
                    total_cmeth_usd=protocol_usd,
                    day_user_count=wallet_count,
                    total_user_count=wallet_count,
                    updated_version=self.version
                )

            )

        self.results.extend(results)

    def get_filter_cmeth_orm(self, orm_class):
        session = self.db_service.Session()
        orm_list = session.query(orm_class).filter(
            orm_class.period_date == self.start_date
        ).filter(
            or_(
                orm_class.token0_symbol == 'cmETH',
                orm_class.token1_symbol == 'cmETH'
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
        address = bytes.fromhex(self.token_address.lower()[2:])

        the_period_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()

        price_dict = get_latest_price(['cmETH'], self.db_service, self.end_date)
        results = {
            (the_period_date, format_value_for_json(r.address)): [float(r.balance / 10 ** 18),
                                                                  float(r.balance * price_dict.get('cmETH',
                                                                                                   0) / 10 ** 18)]
            for r in period_addresses}
        session.close()

        return results

    def get_merchantmoe_json(self):
        orm_list = self.get_filter_cmeth_orm(PeriodFeatureHoldingBalanceMerchantmoeCmeth)
        # results = get_pool_token_pair_data(orm_list, self.token_symbol, self.db_service, self.end_date)
        results = get_pool_token_pair_data_with_lp(orm_list, self.token_symbol, self.db_service, self.end_date,
                                                    'merchantmoe')
        self.get_pool_token_pair_aggr_by_protocol(orm_list, self.price)
        return results

    def get_uniswap_v3_json(self):
        uniswapV3_list = self.get_filter_cmeth_orm(PeriodFeatureHoldingBalanceUniswapV3Cmeth)
        orms = get_new_uniswap_v3_orms(self.start_date)
        uniswapV3_list.extend(orms)
        # results = get_pool_token_pair_data(uniswapV3_list, self.token_symbol, self.db_service, self.end_date)
        results = get_pool_token_pair_data_with_lp(uniswapV3_list, self.token_symbol, self.db_service, self.end_date, 'uniswapv3')
        self.get_pool_token_pair_aggr_by_protocol(uniswapV3_list, self.price)
        return results

    def get_staked_detail_orm_list(self):
        sql = f"""  select 
                            date('{self.start_date}') as period_date,
                            protocol_id,
                           contract_address,
                           wallet_address,
                           token_address,
                           token_symbol,
                           block_cumulative_value / pow(10, decimals) as balance
                    from (select d1.*,
                                 d2.decimals,
                                 d2.symbol as token_symbol,
                                 row_number()
                                 over (partition by contract_address, wallet_address, token_address order by d1.block_number desc) rn
                          from feature_staked_transfer_detail_records d1
                                   inner join tokens d2 on d1.token_address = d2.address
                          where d1.token_address = decode('e6829d9a7ee3040e1276fa75293bde931859e8fa', 'hex')
                            and to_timestamp(block_timestamp) < '{self.end_date}'
                            and  protocol_id <> 'init_capital'
                            ) t
                    where rn = 1 
                """
        session = self.db_service.Session()
        stmt = session.execute(text(sql))
        orm_result = stmt.fetchall()
        return orm_result

    def get_staked_json(self):
        orm_list = self.get_staked_detail_orm_list()

        results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
                                                            self.end_date)
        self.get_token_aggr_by_protocol(orm_list, self.price)

        return results

    def get_token_aggr_by_protocol(self, orm_list, price):
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
                token_usd = float(price * entity.balance)
                balance = float(entity.balance)
                protocol_balance += balance
                protocol_usd += token_usd
                wallet_count += 1

            results.append(
                PeriodFeatureDefiCmethAggregates(
                    period_date=period_date,
                    chain_name=self.chain_name,
                    protocol_id=protocol_id,
                    total_cmeth_balance=protocol_balance,
                    total_cmeth_usd=protocol_usd,
                    day_user_count=wallet_count,
                    total_user_count=wallet_count,
                    updated_version=self.version
                )

            )

        self.results.extend(results)

    def get_lendle_json(self):
        orm_list = get_filter_start_date_orm(PeriodFeatureHoldingBalanceLendle, self.db_service, self.start_date)
        results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
                                                            self.end_date)

        cmeth_orm_list = [r for r in orm_list if r.token_address.hex() == self.token_address[2:]]
        self.get_token_aggr_by_protocol(cmeth_orm_list, self.price)

        return results

    def get_init_capital_json(self):
        orm_list = get_filter_start_date_orm(PeriodFeatureHoldingBalanceInitCapital, self.db_service, self.start_date)
        results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.db_service,
                                                            self.end_date)

        cmeth_orm_list = [r for r in orm_list if r.token_address.hex() == self.token_address[2:]]
        self.get_token_aggr_by_protocol(cmeth_orm_list, self.price)
        return results

    def run(self):
        if self.chain_name == 'mantle':
            uniswap_v3_json = timed_call(self.get_uniswap_v3_json, 'get_uniswap_v3_json')
            merchantmoe_json = timed_call(self.get_merchantmoe_json, 'get_merchantmoe_json')
            staked_json = timed_call(self.get_staked_json, 'get_staked_json')

            lendle_json = timed_call(self.get_lendle_json, 'get_lendle_json')
            init_capital_json = timed_call(self.get_init_capital_json, 'get_init_capital_json')

        else:
            lendle_json = {}
            init_capital_json = {}
            uniswap_v3_json = {}
            staked_json = {}
            merchantmoe_json = {}
        # period_date can be removed from the key
        protocols = [staked_json, merchantmoe_json, uniswap_v3_json, lendle_json, init_capital_json]

        address_token_balances = timed_call(self.get_period_address_token_balances,
                                                 'get_period_address_token_balances')
        protocols_with_address_balance = protocols + [address_token_balances]

        protocol_wallet_keys_list = list({key for d in protocols_with_address_balance for key in d.keys()})

        result_orm_list = []

        for key in protocol_wallet_keys_list:
            total_protocol_cmeth_balance = 0
            total_protocol_cmeth_usd = 0

            wallet_holding_cmeth_balance = 0
            wallet_holding_cmeth_usd = 0

            protocol_holding_detail = []

            address_token_balances_value = address_token_balances.get(key, '')
            if address_token_balances_value:
                wallet_holding_cmeth_balance += address_token_balances_value[0]
                wallet_holding_cmeth_usd += address_token_balances_value[1]

            for protocol in protocols:
                protocol_value = protocol.get(key, '')
                if protocol_value:
                    protocol_holding_detail.extend(protocol_value.get('contract_json'))
                    total_protocol_cmeth_balance += protocol_value.get('balance')
                    total_protocol_cmeth_usd += protocol_value.get('usd')

            period_date, wallet_address = key

            record = PeriodFeatureDefiWalletCmethDetail(
                period_date=period_date,
                wallet_address=format_value_for_json(wallet_address),
                chain_name=self.chain_name,
                contracts=protocol_holding_detail,
                total_protocol_cmeth_balance=total_protocol_cmeth_balance,
                total_protocol_cmeth_usd=total_protocol_cmeth_usd,
                wallet_holding_cmeth_balance=wallet_holding_cmeth_balance,
                updated_version=self.version,
                wallet_holding_cmeth_usd=wallet_holding_cmeth_usd,
                total_cmeth_balance=total_protocol_cmeth_balance + wallet_holding_cmeth_balance,
                total_cmeth_usd=total_protocol_cmeth_usd + wallet_holding_cmeth_usd,
                rank=0

            )
            result_orm_list.append(record)
        result_orm_list.sort(key=attrgetter('period_date', 'total_cmeth_balance'), reverse=True)

        grouped = groupby(result_orm_list, key=attrgetter('period_date'))

        for _, group in grouped:
            for idx, item in enumerate(group, start=1):
                item.rank = idx

        session = self.db_service.Session()

        session.query(PeriodFeatureDefiWalletCmethDetail).filter(
            PeriodFeatureDefiWalletCmethDetail.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(result_orm_list)
        session.commit()
        session.close()

        #     aggr by protocol
        self.insert_aggr_job(self.results)
