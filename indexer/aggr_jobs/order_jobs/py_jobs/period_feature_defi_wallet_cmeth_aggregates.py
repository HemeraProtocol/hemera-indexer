import time
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import attrgetter

from sqlalchemy import func, desc, or_, and_

from common.models.token_price import TokenPrice
from common.utils.format_utils import format_value_for_json
from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_cmeth_detail import \
    PeriodFeatureDefiWalletCmethDetail
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_merchantmoe_cmeth import \
    PeriodFeatureHoldingBalanceMerchantmoeCmeth


class PeriodFeatureDefiWalletCmethAggregates:
    def __init__(self, chain_name, db_service, start_date, end_date, version):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.end_date = end_date
        self.version = version
        self.results = []

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

                        if record.token0_symbol == 'cmETH':
                            total_balance += float(record.token0_balance)
                            total_usd += token_usd0

                        if record.token1_symbol == 'cmETH':
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
        cmeth_address = '0xe6829d9a7ee3040e1276fa75293bde931859e8fa'
        address = bytes.fromhex(cmeth_address.lower()[2:])

        the_period_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()

        price_dict = self.get_latest_price(['cmETH'])
        results = {
            (the_period_date, r.address): [float(r.balance / 10 ** 18), float(r.balance * price_dict.get('cmETH', 0) / 10 ** 18)]
            for r in period_addresses}
        session.close()

        return results

    def get_merchantmoe_json(self):
        orm_list = self.get_filter_cmeth_orm(PeriodFeatureHoldingBalanceMerchantmoeCmeth)
        results = self.get_pool_token_pair_data(orm_list)
        return results

    @staticmethod
    def timed_call(method, method_name):
        start_time = time.time()
        result = method()
        elapsed_time = time.time() - start_time
        print(f'took {elapsed_time:.2f} seconds by {method_name}')
        return result

    def run(self):
        address_token_balances = self.timed_call(self.get_period_address_token_balances,
                                                 'get_period_address_token_balances')


        if self.chain_name == 'mantle':
            merchantmoe_json = self.timed_call(self.get_merchantmoe_json, 'get_merchantmoe_json')
        else:
            merchantmoe_json = {}
        # period_date can be removed from the key
        protocols = [merchantmoe_json]

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
