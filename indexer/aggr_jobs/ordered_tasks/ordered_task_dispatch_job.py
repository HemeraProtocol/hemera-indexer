import time

from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.aggr_jobs.ordered_tasks.py_jobs.period_feature_defi_wallet_fbtc_aggregates import (
    PeriodFeatureDefiWalletFbtcAggregates,
)


class AggrOrderedTaskDispatchJob(AggrBaseJob):
    sql_folder = "ordered_tasks"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        tasks_dict = kwargs["tasks_dict"]
        self.tasks_dict = tasks_dict.get('ordered_tasks', [])
        self.db_service = config["db_service"]

    def generator_py_jobs(self, job_name, start_date, end_date):
        if job_name == "period_feature_defi_wallet_fbtc_aggregates.py":
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

            for job_name in self.tasks_dict:
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
