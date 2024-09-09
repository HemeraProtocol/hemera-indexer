from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor


class AggrDisorderJob(AggrBaseJob):
    sql_folder = "disorder_jobs"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        job_list = kwargs["job_list"]
        self.job_list = job_list.get_disordered_jobs()
        self.db_service = config["db_service"]
        self._batch_work_executor = BatchWorkExecutor(10, 10)

    def run(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]

        execute_sql_list = []
        date_pairs = self.generate_date_pairs(start_date, end_date)
        for date_pair in date_pairs:
            start_date, end_date = date_pair
            # Could be replaced to auto and selected
            for sql_name in self.job_list:
                sql_content = self.get_sql_content(sql_name, start_date, end_date)
                execute_sql_list.append(sql_content)

        self._batch_work_executor.execute(execute_sql_list, self.execute_sql, total_items=len(execute_sql_list))
        self._batch_work_executor.wait()
        print(f"finish disorder job {start_date}")

    def execute_sql(self, sql_contents):
        session = self.db_service.Session()
        for sql_content in sql_contents:
            session.execute(text(sql_content))
            session.commit()
