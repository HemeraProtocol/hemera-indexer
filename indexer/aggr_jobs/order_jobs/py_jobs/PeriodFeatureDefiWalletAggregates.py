from collections import defaultdict
from datetime import datetime

from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_fbtc_aggregates import PeriodFeatureDefiFbtcAggregates
from indexer.aggr_jobs.order_jobs.py_jobs.untils import format_value_for_json


class PeriodFeatureDefiWalletAggregates:
    def __init__(self, chain_name, db_service, start_date, end_date, version):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.end_date = end_date
        self.version = version
        self.results = []
        self.token_symbol = None
        self.decimals = None
        self.price = None

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
            wallet_distinct_list = []

            for entity in entity_list:
                token_usd = float(price * entity.balance)
                balance = float(entity.balance)
                protocol_balance += balance
                protocol_usd += token_usd
                if entity.wallet_address not in wallet_distinct_list:
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
            wallet_distinct_list = []
            for entity in entity_list:
                if entity.wallet_address not in wallet_distinct_list:
                    wallet_distinct_list.append(entity.wallet_address)
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

    def get_period_address_token_balances(self):
        address = bytes.fromhex(self.token_address.lower()[2:])

        the_period_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()
        results = {
            (the_period_date, format_value_for_json(r.address)): [float(r.balance / self.decimals),
                                                                  float(r.balance * self.price / self.decimals)]
            for r in period_addresses}
        session.close()

        return results