"""
This scheduler can handle complex relationship dependencies, etc. The current example shows
AggrDisorderJob -> AggrOrderJob
"""
from indexer.aggr_jobs.disorder_jobs.disorder_job import AggrDisorderJob
from indexer.aggr_jobs.order_jobs.order_job import AggrOrderJob


class AggrJobScheduler:
    def __init__(self, config):
        self.config = config
        self.jobs = self.instantiate_jobs()

    def run_jobs(self, start_date, end_date):
        for job in self.jobs:
            job.run(start_date=start_date, end_date=end_date)

    def instantiate_jobs(self):
        jobs = []
        for job_class in [AggrDisorderJob, AggrOrderJob]:
            job = job_class(
                config=self.config,
            )
            jobs.append(job)
        return jobs
