import time

from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.aggr_jobs.order_jobs.py_jobs.period_feature_defi_wallet_fbtc_aggregates import (
    PeriodFeatureDefiWalletFbtcAggregates,
)


class AggrOrderJob(AggrBaseJob):
    sql_folder = "order_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        job_list = kwargs["job_list"]
        self.job_list = job_list.get_order_jobs()
        self.db_service = config["db_service"]
        self.chain_name = config["chain_name"]

    def generator_py_jobs(self, name, start_date, end_date):
        if name == "period_feature_defi_wallet_fbtc_aggregates.py":
            period_feature_defi_wallet_fbtc_aggregates_job = PeriodFeatureDefiWalletFbtcAggregates(
                self.chain_name, self.db_service, start_date
            )
            period_feature_defi_wallet_fbtc_aggregates_job.run()

    def run(self, **kwargs):
        start_date_limit = kwargs["start_date"]
        end_date_limit = kwargs["end_date"]

        session = self.db_service.Session()

        date_pairs = self.generate_date_pairs(start_date_limit, end_date_limit)
        for date_pair in date_pairs:
            start_date, end_date = date_pair

            for job_name in self.job_list:
                start_time = time.time()
                if job_name.endswith(".py"):
                    self.generator_py_jobs(job_name, start_date, end_date)
                else:
                    sql_content = self.get_sql_content(job_name, start_date, end_date)
                    session.execute(text(sql_content))
                    session.commit()
                execution_time = time.time() - start_time
                print(f"----------- executed in {execution_time:.2f} seconds: JOB {job_name}")

            print("======== finished date", start_date)

        session.close()
