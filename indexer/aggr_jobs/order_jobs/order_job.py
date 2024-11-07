from indexer.aggr_jobs.order_jobs.py_jobs.period_feature_defi_wallet_aggregates import \
    PeriodFeatureDefiWalletFbtcAggregates
from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]
        self.job_list = ['period_address_token_balances.sql', 'period_feature_holding_balance_uniswap_v3.sql']
        self.version = config["version"]

    def run(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date, end_date)
        for date_pair in date_pairs:
            start_date, end_date = date_pair
            for job_name in self.job_list:
                sql_content = self.get_sql_content(job_name, start_date, end_date)
                session.execute(text(sql_content))
                session.commit()

            period_feature_defi_wallet_fbtc_aggregates_job = PeriodFeatureDefiWalletFbtcAggregates('arbitrum',
                                                                                                   self.db_service,
                                                                                                   start_date,
                                                                                                   end_date,
                                                                                                   self.version
                                                                                                   )
            period_feature_defi_wallet_fbtc_aggregates_job.run()
