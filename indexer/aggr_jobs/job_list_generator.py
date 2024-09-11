class JobListGenerator(object):
    def __init__(self, job_name,initialization_jobs, disorder_jobs, order_jobs):
        self.job_name = job_name
        self.initialization_jobs = initialization_jobs
        self.disorder_jobs = disorder_jobs
        self.order_jobs = order_jobs

    def get_initialization_jobs(self):
        return self.initialization_jobs

    def get_disorder_jobs(self):
        return self.disorder_jobs

    def get_order_jobs(self):
        return self.order_jobs
