from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor


class AggrDisorderJob(AggrBaseJob):
    sql_folder = "disorder_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        self.db_service = config["db_service"]
        self._batch_work_executor = BatchWorkExecutor(5, 5)

    def run(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]

        execute_sql_list = []
        date_pairs = self.generate_date_pairs(start_date, end_date)
        for date_pair in date_pairs:
            start_date, end_date = date_pair
            sql_content = self.get_sql_content("daily_wallet_addresses_aggregates", start_date, end_date)
            execute_sql_list.append(sql_content)

        self._batch_work_executor.execute(execute_sql_list, self.execute_sql, total_items=len(execute_sql_list))
        self._batch_work_executor.wait()

    def execute_sql(self, sql_contents):
        session = self.db_service.Session()
        for sql_content in sql_contents:
            session.execute(text(sql_content))
            session.commit()
