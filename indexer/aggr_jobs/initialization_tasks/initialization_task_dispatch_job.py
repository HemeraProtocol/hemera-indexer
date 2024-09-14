import time

from sqlalchemy import text

from indexer.aggr_jobs.aggr_base_job import AggrBaseJob


class InitializationTaskDispatchJob(AggrBaseJob):
    sql_folder = "initialization_tasks"

    def __init__(self, **kwargs):
        config = kwargs["config"]
        tasks_dict = kwargs["tasks_dict"]
        self.tasks_list = tasks_dict.get('initialization_tasks', [])

        self.db_service = config["db_service"]

    def run(self, **kwargs):
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]

        session = self.db_service.Session()
        for job_name in self.tasks_list:
            start_time = time.time()
            sql_content = self.get_sql_content(job_name, self.start_date, self.end_date)
            session.execute(text(sql_content))
            session.commit()
            execution_time = time.time() - start_time
            print(f"----------- executed in {execution_time:.2f} seconds: JOB {job_name}")
        print("======== finished date", self.start_date)
        session.close()
