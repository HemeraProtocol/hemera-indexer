import time

from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.aggr_jobs.order_jobs.py_jobs.period_feature_defi_wallet_cmeth_aggregates import \
    PeriodFeatureDefiWalletCmethAggregates
from indexer.aggr_jobs.order_jobs.py_jobs.period_feature_defi_wallet_fbtc_aggregates import \
    PeriodFeatureDefiWalletFbtcAggregates

from indexer.aggr_jobs.order_jobs.py_jobs.period_wallet_protocol_json_process_cmeth import PeriodWalletProtocolJsonProcessCmeth
from indexer.aggr_jobs.order_jobs.py_jobs.period_wallet_protocol_json_process_fbtc import PeriodWalletProtocolJsonProcessFbtc


# job_list = [
#     'period_address_token_balances',
#     'period_feature_holding_balance_uniswap_v3.sql',
#     'period_feature_staked_fbtc_detail_records.sql',
#     'period_feature_holding_balance_staked_fbtc_detail.sql',  # maybe can be removed
#     'period_feature_holding_balance_staked_transferred_fbtc_detail.sql',
#     'period_feature_erc1155_token_supply_records.sql',
#     'period_feature_holding_balance_merchantmoe.sql',
#     'period_feature_erc20_token_supply_records.sql', 'period_feature_holding_balance_dodo.sql'
# ]
#
# if self.chain_name == 'mantle':
#     if 'period_feature_holding_balance_merchantmoe_cmeth.sql' not in job_list:
#         job_list.append('period_feature_holding_balance_merchantmoe_cmeth.sql')
#
#     if 'period_feature_holding_balance_lendle_au.sql' not in job_list:
#         job_list.append('period_feature_holding_balance_lendle_au.sql')
#
#     if 'period_feature_holding_balance_init_capital.sql' not in job_list:
#         job_list.append('period_feature_holding_balance_init_capital.sql')


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]
        # self.chain_name = config["chain_name"]

        self.version = config["version"]
        jobs_dict = config["jobs_dict"]
        self.chain_name = jobs_dict['chain_name']

        self.job_list = self.get_period_jobs_from_jobs_dict(jobs_dict)

        fbtc = jobs_dict.get('FBTC', {})
        self.fbtc_jobs = fbtc.get('py_jobs')
        self.fbtc_generator_wallet_table = fbtc.get('generator_wallet_table', False)

        cmeth = jobs_dict.get('cmETH', {})
        self.cmeth_jobs = cmeth.get('py_jobs')
        self.cmeth_generator_wallet_table = cmeth.get('generator_wallet_table', False)
        pass

    def get_period_jobs_from_jobs_dict(self, jobs_dict):
        period_sqls = []

        self.extract_sqls_in_order(jobs_dict, 'FBTC', 'period_sqls', period_sqls)
        self.extract_sqls_in_order(jobs_dict, 'cmETH', 'period_sqls', period_sqls)
        return period_sqls

    def run(self, **kwargs):
        start_date_limit = kwargs["start_date"]
        end_date_limit = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date_limit, end_date_limit)
        for date_pair in date_pairs:
            start_date, end_date = date_pair

            for sql_name in self.job_list:
                # continue

                sql_content = self.get_sql_content(sql_name, start_date, end_date)
                start_time = time.time()
                session.execute(text(sql_content))
                session.commit()
                execution_time = time.time() - start_time
                print(f'----------- executed in {execution_time:.2f} seconds: SQL {sql_name}')

            if self.fbtc_jobs or self.fbtc_generator_wallet_table:
                start_time = time.time()
                period_wallet_protocol_json_fbtc = PeriodWalletProtocolJsonProcessFbtc(self.chain_name, self.db_service,
                                                                                       start_date, end_date,
                                                                                       self.version, self.fbtc_jobs,
                                                                                       self.fbtc_generator_wallet_table)

                period_wallet_protocol_json_fbtc.run()
                execution_time = time.time() - start_time
                print(f'----------- executed in {execution_time:.2f} seconds: FBTC')

            if self.cmeth_jobs or self.cmeth_generator_wallet_table:
                start_time = time.time()
                period_wallet_protocol_json_process_cmeth = PeriodWalletProtocolJsonProcessCmeth(self.chain_name,
                                                                                                 self.db_service,
                                                                                                 start_date, end_date,
                                                                                                 self.version,
                                                                                                 self.cmeth_jobs,
                                                                                                 self.cmeth_generator_wallet_table)

                period_wallet_protocol_json_process_cmeth.run()
                execution_time = time.time() - start_time
                print(f'----------- executed in {execution_time:.2f} seconds: cmETH')

        #     # todo: improve the logic between sql and py jobs
        #     period_feature_defi_wallet_fbtc_aggregates_job = PeriodFeatureDefiWalletFbtcAggregates(self.chain_name,
        #                                                                                            self.db_service,
        #                                                                                            start_date,
        #                                                                                            end_date,
        #                                                                                            self.version
        #                                                                                            )
        #
        #     start_time = time.time()
        #     # period_feature_defi_wallet_fbtc_aggregates_job.run()
        #     execution_time = time.time() - start_time
        #     print(f'----------- executed in {execution_time:.2f} seconds: FBTC')
        #
        #     if self.chain_name == 'mantle':
        #         start_time = time.time()
        #         period_feature_defi_wallet_cmeth_aggregates_job = PeriodFeatureDefiWalletCmethAggregates(
        #             self.chain_name,
        #             self.db_service,
        #             start_date,
        #             end_date,
        #             self.version
        #         )
        #         # period_feature_defi_wallet_cmeth_aggregates_job.run()
        #         execution_time = time.time() - start_time
        #         print(f'----------- executed in {execution_time:.2f} seconds: CMETH')
        #
        #         print('======== finished date', start_date)
        #
        # session.close()
