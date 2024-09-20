import time

from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.aggr_jobs.order_jobs.py_jobs.period_feature_defi_wallet_fbtc_aggregates import \
    PeriodFeatureDefiWalletFbtcAggregates

job_list = ['period_address_token_balances', 'period_feature_holding_balance_uniswap_v3.sql',
            'period_feature_staked_fbtc_detail_records.sql',
            'period_feature_holding_balance_satlayer_fbtc.sql',
            'period_feature_holding_balance_staked_fbtc_detail.sql',
            # 'period_feature_erc1155_token_holdings.sql',
            'period_feature_erc1155_token_supply_records.sql', 'period_feature_holding_balance_merchantmoe.sql',
            'period_feature_erc20_token_supply_records.sql', 'period_feature_holding_balance_dodo.sql',
            'period_feature_holding_balance_lendle.sql'
            ]


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]
        self.chain_name = config["chain_name"]
        self.version = config["version"]

    def run(self, **kwargs):
        start_date_limit = kwargs["start_date"]
        end_date_limit = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date_limit, end_date_limit)
        for date_pair in date_pairs:
            start_date, end_date = date_pair

            for sql_name in job_list:
                sql_content = self.get_sql_content(sql_name, start_date, end_date)
                start_time = time.time()
                session.execute(text(sql_content))
                session.commit()
                execution_time = time.time() - start_time
                print(f'----------- executed in {execution_time:.2f} seconds: SQL {sql_name}')

            # todo: improve the logic between sql and py jobs
            period_feature_defi_wallet_fbtc_aggregates_job = PeriodFeatureDefiWalletFbtcAggregates(self.chain_name,
                                                                                                   self.db_service,
                                                                                                   start_date,
                                                                                                   end_date,
                                                                                                   self.version
                                                                                                   )
            period_feature_defi_wallet_fbtc_aggregates_job.run()
            print('======== finished date', start_date)

        session.close()
