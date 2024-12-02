import logging
import os
import time
from collections import defaultdict
from typing import List

import mpire

from common.utils.exception_control import FastShutdownError
from common.utils.file_utils import delete_file, write_to_file
from indexer.controller.base_controller import BaseController
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.utils.buffer_service import BufferService
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.limit_reader import LimitReader
from indexer.utils.sync_recorder import BaseRecorder

exception_recorder = ExceptionRecorder()

logger = logging.getLogger(__name__)


class StreamController(BaseController):

    def __init__(
        self,
        sync_recorder: BaseRecorder,
        job_scheduler: JobScheduler,
        item_exporters,
        required_output_types,
        limit_reader: LimitReader,
        max_retries=5,
        retry_from_record=False,
        delay=0,
        process_numbers=1,
        process_size=None,
        process_time_out=None,
    ):
        self.entity_types = 1
        self.required_output_types = [output.type() for output in required_output_types]
        self.buffer_service = BufferService(
            item_exporters=item_exporters,
            required_output_types=self.required_output_types,
            export_workers=5,
            block_size=100,
            success_callback=self.handle_success,
            exception_callback=self.handle_failure,
        )

        self.sync_recorder = sync_recorder
        self.job_scheduler = job_scheduler
        self.limit_reader = limit_reader
        self.max_retries = max_retries
        self.retry_from_record = retry_from_record
        self.delay = delay

        self.process_numbers = process_numbers
        self.process_size = process_size
        self.process_time_out = process_time_out

        self.pool = mpire.WorkerPool(n_jobs=self.process_numbers, use_dill=True, keep_alive=True)

    def handle_success(self, last_block_number):
        self.sync_recorder.set_last_synced_block(last_block_number)
        logger.info("Writing last synced block {}".format(last_block_number))

    def handle_failure(
        self, output_types: List[str], start_block: int, end_block: int, exception_stage: str, exception: str
    ):
        self.sync_recorder.set_failure_record(output_types, start_block, end_block, exception_stage, exception)

    def action(
        self,
        start_block=None,
        end_block=None,
        block_batch_size=10,
        period_seconds=10,
        retry_errors=True,
        pid_file=None,
    ):
        try:
            if pid_file is not None:
                logger.debug("Creating pid file {}".format(pid_file))
                write_to_file(pid_file, str(os.getpid()))

            last_synced_block = self.sync_recorder.get_last_synced_block()

            if start_block is not None:
                if (
                    not self.retry_from_record
                    or last_synced_block < start_block
                    or (end_block is not None and last_synced_block > end_block)
                ):
                    last_synced_block = start_block - 1

            while True and (end_block is None or last_synced_block < end_block):
                synced_blocks = 0

                current_block = self.limit_reader.get_current_block_number()
                if current_block is None:
                    raise FastShutdownError(
                        "Can't get current limit block number from limit reader."
                        "If you're using PGLimitReader, please confirm blocks table has one record at least."
                    )

                target_block = self._calculate_target_block(
                    current_block, last_synced_block, end_block, block_batch_size
                )
                synced_blocks = max(target_block - last_synced_block, 0)

                logger.info(
                    "Current block {}, target block {}, last synced block {}, blocks to sync {}".format(
                        current_block, target_block, last_synced_block, synced_blocks
                    )
                )

                if synced_blocks != 0:
                    # submit job and concurrent running

                    splits = self.split_blocks(last_synced_block + 1, target_block, self.process_size)
                    export_data = defaultdict(list)
                    for result in list(
                        self.pool.map(func=self._do_stream, iterable_of_args=splits, task_timeout=self.process_time_out)
                    ):
                        for key in result:
                            export_data[key].extend(result[key])

                    self.buffer_service.write(export_data)
                    last_synced_block = target_block

                if synced_blocks <= 0:
                    logger.debug("Nothing to sync. Sleeping for {} seconds...".format(period_seconds))
                    time.sleep(period_seconds)
        except Exception as e:
            self.shutdown()
            raise e

        finally:
            if pid_file is not None:
                logger.debug("Deleting pid file {}".format(pid_file))
                delete_file(pid_file)

    def _shutdown(self):
        self.buffer_service.shutdown()

    def split_blocks(self, start_block, end_block, step):
        blocks = []
        for i in range(start_block, end_block + 1, step):
            blocks.append((i, min(i + step - 1, end_block)))
        return blocks

    def _do_stream(self, start_block, end_block):
        return self.job_scheduler.run_jobs(start_block, end_block)

    def _calculate_target_block(self, current_block, last_synced_block, end_block, steps):
        target_block = min(current_block - self.delay, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.pool.terminate()
        except Exception:
            pass
