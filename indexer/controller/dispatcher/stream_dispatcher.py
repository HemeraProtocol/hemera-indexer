import logging

from enumeration.record_level import RecordLevel
from indexer.controller.dispatcher.base_dispatcher import BaseDispatcher
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.utils.exception_recorder import ExceptionRecorder

exception_recorder = ExceptionRecorder()


class StreamDispatcher(BaseDispatcher):

    def __init__(
        self,
        service,
        batch_web3_provider,
        batch_web3_debug_provider,
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        required_output_types=[],
        config={},
        cache=None,
    ):
        super().__init__(service)
        self._job_scheduler = JobScheduler(
            batch_web3_provider=batch_web3_provider,
            batch_web3_debug_provider=batch_web3_debug_provider,
            item_exporters=item_exporters,
            batch_size=batch_size,
            debug_batch_size=debug_batch_size,
            max_workers=max_workers,
            config=config,
            required_output_types=required_output_types,
            cache=cache,
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Export output types: %s", required_output_types)

    def run(self, start_block, end_block):
        try:
            self._job_scheduler.run_jobs(
                start_block=start_block,
                end_block=end_block,
            )

            for key, value in self._job_scheduler.get_data_buff().items():
                message = f"{key}: {len(value)}"
                self.logger.info("Export dataclass detail: %s", message)
                exception_recorder.log(
                    block_number=-1, dataclass=key, message_type="item_counter", message=message, level=RecordLevel.INFO
                )

            exception_recorder.force_to_flush()

        except Exception as e:
            raise e
        finally:
            self._job_scheduler.clear_data_buff()
