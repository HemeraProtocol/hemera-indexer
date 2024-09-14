"""
This scheduler can handle complex relationship dependencies, etc. The current example shows
AggrDisorderJob -> AggrOrderJob
"""

from indexer.aggr_jobs.regular_tasks.regular_task_dispatch_job import AggrRegularTaskDispatchJob
from indexer.aggr_jobs.initialization_tasks.initialization_task_dispatch_job import InitializationTaskDispatchJob
from indexer.aggr_jobs.ordered_tasks.ordered_task_dispatch_job import AggrOrderedTaskDispatchJob


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
        for job_class in [InitializationTaskDispatchJob, AggrRegularTaskDispatchJob, AggrOrderedTaskDispatchJob]:
            job = job_class(config=self.config, job_list=self.job_list)
            jobs.append(job)
        return jobs
