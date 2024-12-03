import warnings
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import attrgetter

from sqlalchemy import or_, and_, text

from indexer.aggr_jobs.order_jobs.models.period_address_token_balances import PeriodAddressTokenBalances
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_cmeth_aggregates import PeriodFeatureDefiCmethAggregates
from indexer.aggr_jobs.order_jobs.models.period_feature_defi_wallet_cmeth_detail import \
    PeriodFeatureDefiWalletCmethDetail
from indexer.aggr_jobs.order_jobs.models.period_wallet_protocol_json_cmeth import PeriodWalletProtocolJsonCmeth
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_init_capital import \
    PeriodFeatureHoldingBalanceInitCapital
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_lendle import PeriodFeatureHoldingBalanceLendle
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_merchantmoe_cmeth import \
    PeriodFeatureHoldingBalanceMerchantmoeCmeth
from indexer.aggr_jobs.order_jobs.models.period_feature_holding_balance_uniswap_v3 import \
    PeriodFeatureHoldingBalanceUniswapV3Cmeth
from indexer.aggr_jobs.order_jobs.py_jobs.uniswapv3_job import get_detail_df, calculate_liquidity, change_df_to_obj, \
    get_uniswap_v3_orms_from_old_mantle, get_uniswap_v3_orms_from_new_mantle
from indexer.aggr_jobs.order_jobs.py_jobs.untils import format_value_for_json, get_new_uniswap_v3_orms, \
    get_token_data_for_lendle_au_init_capital, get_filter_start_date_orm, \
    get_pool_token_pair_data_with_lp, timed_call, get_last_block_number_before_end_date, timed_call_

warnings.filterwarnings('ignore', category=FutureWarning)


class PeriodWalletProtocolJsonProcessCmeth:
    def __init__(self, chain_name, db_service, start_date, end_date, version, job_list, common_dict, generator_wallet_table=False):
        self.chain_name = chain_name
        self.db_service = db_service
        self.start_date = start_date
        self.end_date = end_date
        self.version = version
        self.job_list = job_list
        self.results = []
        self.generator_wallet_table = generator_wallet_table

        self.token_address = '0xe6829d9a7ee3040e1276fa75293bde931859e8fa'
        self.token_symbol = 'cmETH'
        self.decimals = 10 ** 18

        self.price_dict = common_dict.get('price_dict')
        self.last_block_number = common_dict.get('last_block_number')
        self.price = self.price_dict.get(self.token_symbol, 0)

        # self._new_session = get_engine()

    @staticmethod
    def filter_instance_data(instance):
        """
        从 SQLAlchemy 实例中提取模型字段的字典表示。
        """
        return {
            column.name: getattr(instance, column.name)
            for column in instance.__table__.columns
        }

    def insert_aggr_job(self):
        existing_results = self.get_protocol_aggr()
        results_protocol_id_list = [r.protocol_id for r in self.results]

        existing_results_copy = [PeriodFeatureDefiCmethAggregates(**self.filter_instance_data(r)) for r in
                                 existing_results]

        for existing_result in existing_results_copy:
            if existing_result.protocol_id not in results_protocol_id_list:
                self.results.append(existing_result)

        session = self.db_service.Session()

        session.query(PeriodFeatureDefiCmethAggregates).filter(
            PeriodFeatureDefiCmethAggregates.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(self.results)
        session.commit()
        print(f'insert {self.token_symbol} successfully, {len(self.results)}')
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

    def get_staked_data_from_address_token_balance(self):
        sql = f"""
        select date('{self.start_date}')                           as period_date,
       'thetanuts'                                  as protocol_id,
       '0xdee7cb1d08ec5e35c4792856f86dd0584db29cfe' as contract_address,
       address                                      as wallet_address,
       '0xe6829d9a7ee3040e1276fa75293bde931859e8fa' as token_address,
       'cmETH'                                      as token_symbol,
       balance / pow(10, 18)                        as balance
        from period_address_token_balances
where token_address = decode('dee7cb1d08ec5e35c4792856f86dd0584db29cfe', 'hex')
union all 
        select date('{self.start_date}')                           as period_date,
       'hour_glass'                                      as protocol_id,
       '0x37e3ac623b488bb075ce8f3199ae93f8cac727f2' as contract_address,
       address                                      as wallet_address,
        '0xe6829d9a7ee3040e1276fa75293bde931859e8fa' as token_address,
       'cmETH'                                      as token_symbol,
       balance / pow(10, 18)                        as balance
from period_address_token_balances
where token_address = decode('326b1129a3ec2ad5c4016d2bb4b912687890ae6c', 'hex')

-- woofi
        union all
        select date('{self.start_date}')                           as period_date,
               'woofi'                                      as protocol_id,
               '0x82fde5086784e348aed03eb7b19ded97652db7a8' as contract_address,
               address                                      as wallet_address,
        '0xe6829d9a7ee3040e1276fa75293bde931859e8fa' as token_address,
               'cmETH'                                      as token_symbol,
               balance / pow(10, 18)                        as balance
        from period_address_token_balances
where token_address = decode('872b6ff825da431c941d12630754036278ad7049', 'hex')
union all 

select  date('{self.start_date}')                           as period_date,
       protocol_id,
       '0x82fde5086784e348aed03eb7b19ded97652db7a8' as contract_address,
       wallet_address,
       '0xe6829d9a7ee3040e1276fa75293bde931859e8fa' as token_address,
       'cmETH'                                      as token_symbol,
       block_cumulative_value / pow(10, 18)         as balance
from (select *,
             row_number()
             over (partition by contract_address, wallet_address, token_address order by block_number desc) rn
      from feature_staked_transfer_detail_records
      where protocol_id = 'woofi'
        and token_address = decode('872b6ff825da431c941d12630754036278ad7049', 'hex')
        and to_timestamp(block_timestamp) < '{self.end_date}') t
where rn = 1;
        """
        session = self.db_service.Session()
        stmt = session.execute(text(sql))
        orm_result = stmt.fetchall()
        return orm_result

    def get_period_address_token_balances(self):
        address = bytes.fromhex(self.token_address.lower()[2:])

        # the_period_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        session = self.db_service.Session()

        period_addresses = session.query(PeriodAddressTokenBalances).filter(
            PeriodAddressTokenBalances.token_address == address).all()
        results = {format_value_for_json(r.address): [float(r.balance / self.decimals),
                                                      float(r.balance * self.price / self.decimals)]
                   for r in period_addresses}
        session.close()

        return results

    def get_merchantmoe_json(self):
        protocol_id = 'merchantmoe'
        if protocol_id in self.job_list:
            orm_list = self.get_filter_cmeth_orm(PeriodFeatureHoldingBalanceMerchantmoeCmeth)
            # results = get_pool_token_pair_data(orm_list, self.token_symbol, self.db_service, self.end_date)
            results = get_pool_token_pair_data_with_lp(orm_list, self.token_symbol, self.db_service, self.end_date, self.price_dict,
                                                       'merchantmoe')
            self.insert_protocol_json(protocol_id, results)

            self.get_pool_token_pair_aggr_by_protocol(orm_list, self.price)

    def get_uniswap_v3_json(self):
        uniswapV3_list = self.get_filter_cmeth_orm(PeriodFeatureHoldingBalanceUniswapV3Cmeth)
        orms = get_new_uniswap_v3_orms(self.start_date)
        uniswapV3_list.extend(orms)
        # results = get_pool_token_pair_data(uniswapV3_list, self.token_symbol, self.db_service, self.end_date)
        results = get_pool_token_pair_data_with_lp(uniswapV3_list, self.token_symbol, self.db_service, self.end_date,self.price_dict,
                                                   'uniswapv3')
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
        protocol_id = 'staked'
        if protocol_id in self.job_list:
            # all tokens are cmeth
            orm_list = self.get_staked_detail_orm_list()

            # all tokens are cmeth
            staked_token_orm_list = self.get_staked_data_from_address_token_balance()
            orm_list.extend(staked_token_orm_list)

            # need to filter the only token in some cases
            results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.price_dict)

            self.insert_protocol_json(protocol_id, results)
            self.get_token_aggr_by_protocol(orm_list, self.price)

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
        protocol_id = 'lendle'
        if protocol_id in self.job_list:
            # all tokens
            orm_list = get_filter_start_date_orm(PeriodFeatureHoldingBalanceLendle, self.db_service, self.start_date)
            results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.price_dict)

            self.insert_protocol_json(protocol_id, results)

            cmeth_orm_list = [r for r in orm_list if r.token_address.hex() == self.token_address[2:]]

            self.get_token_aggr_by_protocol(cmeth_orm_list, self.price)

    def get_init_capital_json(self):
        protocol_id = 'init_capital'
        if protocol_id in self.job_list:
            # all tokens
            orm_list = get_filter_start_date_orm(PeriodFeatureHoldingBalanceInitCapital, self.db_service,
                                                 self.start_date)
            results = get_token_data_for_lendle_au_init_capital(orm_list, self.token_address, self.price_dict)
            self.insert_protocol_json(protocol_id, results)

            cmeth_orm_list = [r for r in orm_list if r.token_address.hex() == self.token_address[2:]]
            self.get_token_aggr_by_protocol(cmeth_orm_list, self.price)

    def get_uniswapv3_token_data(self):
        protocol_id = 'uniswapv3'
        if protocol_id in self.job_list:
            result = get_uniswap_v3_orms_from_old_mantle(self.db_service, self.start_date)
            df = get_detail_df(result)
            liquidity_df = calculate_liquidity(df, self.token_symbol)
            results1 = change_df_to_obj(liquidity_df)

            result = get_uniswap_v3_orms_from_new_mantle(self.start_date)
            df = get_detail_df(result)
            liquidity_df = calculate_liquidity(df, self.token_symbol)
            results2 = change_df_to_obj(liquidity_df)
            results1.extend(results2)

            results = get_pool_token_pair_data_with_lp(results1, self.token_symbol, self.db_service, self.end_date,self.price_dict,
                                                       'uniswapv3')

            self.insert_protocol_json(protocol_id, results)
            self.get_pool_token_pair_aggr_by_protocol(results1, self.price)

    def get_protocol_aggr(self, protocol_id_list=[]):
        session = self.db_service.Session()
        orms = session.query(PeriodFeatureDefiCmethAggregates).filter(
            PeriodFeatureDefiCmethAggregates.period_date == self.start_date,
            PeriodFeatureDefiCmethAggregates.chain_name == self.chain_name,
            # seems not need
            # PeriodFeatureDefiCmethAggregates.protocol_id.in_(protocol_id_list)
        ).all()
        session.close()
        return orms

    def get_protocol_json(self, protocol_id=None):
        session = self.db_service.Session()
        try:
            # 构造查询对象
            query = session.query(PeriodWalletProtocolJsonCmeth).filter(
                PeriodWalletProtocolJsonCmeth.period_date == self.start_date,
                PeriodWalletProtocolJsonCmeth.chain_name == self.chain_name,
                PeriodWalletProtocolJsonCmeth.token_symbol == self.token_symbol
            )

            # 如果传入了 protocol_id，则追加过滤条件
            if protocol_id is not None:
                query = query.filter(PeriodWalletProtocolJsonCmeth.protocol_id == protocol_id)

            # 执行查询
            orms = query.all()

        finally:
            session.close()

        results = defaultdict(dict)

        for orm in orms:
            results[orm.wallet_address][orm.protocol_id] = {'contract_json': orm.contracts,
                                                            'balance': format_value_for_json(
                                                                orm.total_protocol_balance),
                                                            'usd': format_value_for_json(orm.total_protocol_usd)}
        session.close()
        return results

    def insert_protocol_json(self, protocol_id, protocol_json):
        session = self.db_service.Session()
        # results[(period_date, wallet_address)] = {'contract_json': wallet_address_json, 'balance': total_balance,
        #                                           'usd': total_usd}
        results = []

        for period_date_wallet_address, json_dict in protocol_json.items():
            period_date, wallet_address = period_date_wallet_address
            total_balance = json_dict.get('balance')
            total_usd = json_dict.get('usd')
            contract_json = json_dict.get('contract_json')

            period_wallet_protocol_json_cmeth = PeriodWalletProtocolJsonCmeth(period_date=period_date,
                                                                              wallet_address=wallet_address,
                                                                              chain_name=self.chain_name,
                                                                              token_symbol=self.token_symbol,
                                                                              total_protocol_balance=total_balance,
                                                                              total_protocol_usd=total_usd,
                                                                              contracts=contract_json,
                                                                              protocol_id=protocol_id,
                                                                              updated_version=self.version)

            results.append(period_wallet_protocol_json_cmeth)

        session.query(PeriodWalletProtocolJsonCmeth).filter(
            PeriodWalletProtocolJsonCmeth.period_date == self.start_date,
            PeriodWalletProtocolJsonCmeth.chain_name == self.chain_name,
            PeriodWalletProtocolJsonCmeth.token_symbol == self.token_symbol,
            PeriodWalletProtocolJsonCmeth.protocol_id == protocol_id
        ).delete()

        session.bulk_save_objects(results)
        session.commit()
        print(f'insert {protocol_id} successfully, {len(results)}')
        session.close()

    def insert_wallet_detail(self, result_orm_list):
        session = self.db_service.Session()

        session.query(PeriodFeatureDefiWalletCmethDetail).filter(
            PeriodFeatureDefiWalletCmethDetail.period_date == self.start_date
        ).delete()

        session.bulk_save_objects(result_orm_list)
        session.commit()
        session.close()

    def process_wallet_record(self):
        wallet_protocols = self.get_protocol_json()

        address_token_balances = timed_call(self.get_period_address_token_balances,
                                            'get_period_address_token_balances')

        protocol_wallet_keys_list = list(set(wallet_protocols.keys()).union(address_token_balances.keys()))

        result_orm_list = []

        for key in protocol_wallet_keys_list:
            total_protocol_cmeth_balance = 0
            total_protocol_cmeth_usd = 0

            wallet_holding_cmeth_balance = 0
            wallet_holding_cmeth_usd = 0

            protocol_holding_detail = []

            address_token_balances_value = address_token_balances.get(key)
            if address_token_balances_value:
                wallet_holding_cmeth_balance += address_token_balances_value[0]
                wallet_holding_cmeth_usd += address_token_balances_value[1]

            protocols = wallet_protocols.get(key, {})
            for _, protocol_value in protocols.items():
                if protocol_value:
                    protocol_holding_detail.extend(protocol_value.get('contract_json'))
                    total_protocol_cmeth_balance += protocol_value.get('balance')
                    total_protocol_cmeth_usd += protocol_value.get('usd')

            period_date = self.start_date
            wallet_address = key

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
                rank=0,
                block_number=self.last_block_number,
            )
            result_orm_list.append(record)
        result_orm_list.sort(key=attrgetter('period_date', 'total_cmeth_balance'), reverse=True)

        grouped = groupby(result_orm_list, key=attrgetter('period_date'))

        for _, group in grouped:
            for idx, item in enumerate(group, start=1):
                item.rank = idx

        return result_orm_list

    def process_middle_json(self):
        if self.chain_name == 'mantle':
            timed_call_(self.get_staked_json)
            timed_call_(self.get_lendle_json)
            timed_call_(self.get_uniswapv3_token_data)
            timed_call_(self.get_merchantmoe_json)
            timed_call_(self.get_init_capital_json)

    def run(self):
        self.process_middle_json()
        if self.generator_wallet_table:
            result_orm_list = self.process_wallet_record()
            self.insert_wallet_detail(result_orm_list)
            self.insert_aggr_job()
