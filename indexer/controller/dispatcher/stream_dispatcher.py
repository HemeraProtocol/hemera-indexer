from indexer.controller.dispatcher.base_dispatcher import BaseDispatcher
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler


class StreamDispatcher(BaseDispatcher):

    def __init__(self,
                 service,
                 batch_web3_provider,
                 batch_web3_debug_provider,
                 item_exporter=ConsoleItemExporter(),
                 batch_size=100,
                 debug_batch_size=1,
                 max_workers=5,
                 config=None,
                 required_output_types=[]
                 ):
        super().__init__(service)
        self._job_scheduler = JobScheduler(
            batch_web3_provider=batch_web3_provider,
            batch_web3_debug_provider=batch_web3_debug_provider,
            item_exporter=item_exporter,
            batch_size=batch_size,
            debug_batch_size=debug_batch_size,
            max_workers=max_workers,
            config=config,
            required_output_types=required_output_types,
        )

    def run(self, start_block, end_block):
        self._job_scheduler.run_jobs(
            start_block=start_block,
            end_block=end_block,
        )

        self._job_scheduler.clear_data_buff()
