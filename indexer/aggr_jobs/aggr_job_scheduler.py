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
        self.init_job = {}
        self.jobs = {}
        self.instantiate_jobs()
        pass

    def run_init_job(self, start_date, end_date):
        for job_name, job in self.init_job.items():
            job.run(start_date=start_date, end_date=end_date)

    def run_jobs(self, start_date, end_date):
        for job_name, jobs in self.jobs.items():
            for job in jobs:
                job.run(start_date=start_date, end_date=end_date)

    def instantiate_jobs(self):
        for job_name, tasks_dict in self.job_list.items():
            self.init_job[job_name] = InitializationTaskDispatchJob(config=self.config, tasks_dict=tasks_dict)

            jobs = []
            for job_class in [AggrRegularTaskDispatchJob, AggrOrderedTaskDispatchJob]:
                job = job_class(config=self.config, tasks_dict=tasks_dict)
                jobs.append(job)
            self.jobs[job_name] = jobs
