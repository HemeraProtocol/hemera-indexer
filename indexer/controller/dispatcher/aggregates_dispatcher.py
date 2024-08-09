from indexer.aggr_jobs.aggr_job_scheduler import AggrJobScheduler
from indexer.controller.dispatcher.base_dispatcher import BaseDispatcher


class AggregatesDispatcher(BaseDispatcher):
    def __init__(self, config):
        super().__init__()
        self._job_scheduler = AggrJobScheduler(config=config)

    def run(self, start_date, end_date):
        self._job_scheduler.run_jobs(
            start_date=start_date, end_date=end_date
        )
