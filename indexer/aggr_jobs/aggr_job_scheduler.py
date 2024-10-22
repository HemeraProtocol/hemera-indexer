"""
This scheduler can handle complex relationship dependencies, etc. The current example shows
AggrDisorderJob -> AggrOrderJob
"""

from indexer.aggr_jobs.disorder_jobs.disorder_job import AggrDisorderJob
from indexer.aggr_jobs.initialization_jobs.initialization_job import InitializationJob
from indexer.aggr_jobs.order_jobs.order_job import AggrOrderJob


class AggrJobScheduler:
    def __init__(self, config, job_list):
        self.config = config
        self.job_list = job_list
        self.jobs = self.instantiate_jobs()

    def run_jobs(self, start_date, end_date):
        for job in self.jobs:
            job.run(start_date=start_date, end_date=end_date)

    def instantiate_jobs(self):
        jobs = []
        # InitializationJob should be executed once only
        for job_class in [InitializationJob, AggrDisorderJob, AggrOrderJob]:
            job = job_class(config=self.config, job_list=self.job_list)
            jobs.append(job)
        return jobs
