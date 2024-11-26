from collections import defaultdict
from datetime import datetime

from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_cmeth_aggregates import PeriodFeatureDefiCmethAggregates
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_fbtc_aggregates import PeriodFeatureDefiFbtcAggregates
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_cmeth_detail import \
    PeriodFeatureDefiWalletCmethDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_fbtc_detail import PeriodFeatureDefiWalletFbtcDetail
from indexer.aggr_jobs.order_jobs.models.period_wallet_protocol_json_cmeth import PeriodWalletProtocolJsonCmeth
from indexer.aggr_jobs.order_jobs.models.period_wallet_protocol_json_fbtc import PeriodWalletProtocolJsonFbtc
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
        self.token_address = None

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

        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()
        results = {
            format_value_for_json(r.address): [float(r.balance / self.decimals),
                                               float(r.balance * self.price / self.decimals)]
            for r in period_addresses}
        session.close()

        return results

    def get_token_data_old(self, orm_list):

        wallet_protocol_contract_group = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for record in orm_list:
            period_date_key = record.period_date
            wallet_key = format_value_for_json(record.wallet_address)
            protocol_key = record.protocol_id
            contract_key = record.contract_address

            wallet_protocol_contract_group[(period_date_key, wallet_key)][protocol_key][contract_key].append(record)

        self.get_token_aggr_by_protocol(orm_list, self.price)

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
                        token0_used = float(self.price * record.balance)

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

    # add step to store json data
    def get_protocol_json(self):
        if self.token_symbol == 'cmETH':
            ORM = PeriodWalletProtocolJsonCmeth
        elif self.token_symbol == 'FBTC':
            ORM = PeriodWalletProtocolJsonFbtc
        else:
            return {}

        session = self.db_service.Session()
        orms = session.query(ORM).filter(
            ORM.period_date == self.start_date,
            ORM.chain_name == self.chain_name,
            ORM.token_symbol == self.token_symbol).all()

        results = defaultdict(dict)

        for orm in orms:
            results[orm.wallet_address][orm.protocol_id] = {'contract_json': orm.contracts,
                                                            'balance': format_value_for_json(
                                                                orm.total_protocol_balance),
                                                            'usd': format_value_for_json(orm.total_protocol_usd)}
        session.close()
        return results

    def insert_protocol_json(self, protocol_id, protocol_json):
        if self.token_symbol == 'cmETH':
            ORM = PeriodWalletProtocolJsonCmeth
        elif self.token_symbol == 'FBTC':
            ORM = PeriodWalletProtocolJsonFbtc
        else:
            return {}

        session = self.db_service.Session()
        results = []

        for period_date_wallet_address, json_dict in protocol_json.items():
            period_date, wallet_address = period_date_wallet_address
            total_balance = json_dict.get('balance')
            total_usd = json_dict.get('usd')
            contract_json = json_dict.get('contract_json')

            period_wallet_protocol_json = ORM(period_date=period_date,
                                              wallet_address=wallet_address,
                                              chain_name=self.chain_name,
                                              token_symbol=self.token_symbol,
                                              total_protocol_balance=total_balance,
                                              total_protocol_usd=total_usd,
                                              contracts=contract_json,
                                              protocol_id=protocol_id,
                                              updated_version=self.version
                                              )

            results.append(period_wallet_protocol_json)

        session.query(ORM).filter(
            ORM.period_date == self.start_date,
            ORM.chain_name == self.chain_name,
            ORM.token_symbol == self.token_symbol,
            ORM.protocol_id == protocol_id
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert {protocol_id} successfully, {len(results)}')
        session.close()

    def get_protocol_aggr(self):
        if self.token_symbol == 'cmETH':
            ORM = PeriodFeatureDefiCmethAggregates
        elif self.token_symbol == 'FBTC':
            ORM = PeriodFeatureDefiFbtcAggregates

        session = self.db_service.Session()
        orms = session.query(ORM).filter(
            ORM.period_date == self.start_date,
            ORM.chain_name == self.chain_name,
        ).all()
        session.close()
        return orms

    def insert_wallet_detail(self, result_orm_list):
        if self.token_symbol == 'cmETH':
            ORM = PeriodFeatureDefiWalletCmethDetail
        elif self.token_symbol == 'FBTC':
            ORM = PeriodFeatureDefiWalletFbtcDetail

        session = self.db_service.Session()
        session.query(ORM).filter(
            ORM.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(result_orm_list)
        session.commit()
        session.close()

    def insert_aggr_job(self):
        if self.token_symbol == 'cmETH':
            ORM = PeriodFeatureDefiCmethAggregates
        elif self.token_symbol == 'FBTC':
            ORM = PeriodFeatureDefiFbtcAggregates

        existing_results = self.get_protocol_aggr()
        results_protocol_id_list = [r.protocol_id for r in self.results]

        existing_results_copy = [ORM(**self.filter_instance_data(r)) for r in
                                 existing_results]

        for existing_result in existing_results_copy:
            if existing_result.protocol_id not in results_protocol_id_list:
                self.results.append(existing_result)

        session = self.db_service.Session()

        session.query(ORM).filter(
            ORM.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(self.results)
        session.commit()
        print(f'insert {self.token_symbol} successfully, {len(self.results)}')
        session.close()

    @staticmethod
    def filter_instance_data(instance):
        """
        从 SQLAlchemy 实例中提取模型字段的字典表示。
        """
        return {
            column.name: getattr(instance, column.name)
            for column in instance.__table__.columns
        }
