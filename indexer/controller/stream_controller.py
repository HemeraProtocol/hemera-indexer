import logging
import os
import time
from typing import List

from common.utils.exception_control import FastShutdownError, HemeraBaseException
from common.utils.file_utils import delete_file, write_to_file
from indexer.controller.base_controller import BaseController
from indexer.jobs.base_job import BaseJob
from indexer.utils.data_service import BufferService
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.limit_reader import LimitReader
from indexer.utils.sync_recorder import BaseRecorder

exception_recorder = ExceptionRecorder()

logger = logging.getLogger(__name__)


class StreamController(BaseController):

    def __init__(
        self,
        sync_recorder: BaseRecorder,
        scheduled_jobs: List[BaseJob],
        item_exporters,
        required_output_types,
        limit_reader: LimitReader,
        max_retries=5,
        retry_from_record=False,
        delay=0,
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
        self.scheduled_jobs = scheduled_jobs
        self.limit_reader = limit_reader
        self.max_retries = max_retries
        self.retry_from_record = retry_from_record
        self.delay = delay

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
                    export_data = run_jobs(
                        jobs=self.scheduled_jobs,
                        start_block=last_synced_block + 1,
                        end_block=target_block,
                        max_retries=self.max_retries,
                    )
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

    def _calculate_target_block(self, current_block, last_synced_block, end_block, steps):
        target_block = min(current_block - self.delay, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block


def run_jobs(jobs, start_block, end_block, max_retries):
    try:
        logger.info(f"Task begin, run block range between {start_block} and {end_block}")
        jobs_export_data = {}
        for job in jobs:
            job_export_data = job_with_retires(
                job, start_block=start_block, end_block=end_block, max_retries=max_retries
            )
            jobs_export_data.update(job_export_data)
    except Exception as e:
        raise e

    return jobs_export_data


def job_with_retires(job, start_block, end_block, max_retries):
    for retry in range(max_retries):
        try:
            logger.info(f"Task run {job.__class__.__name__}")
            return job.run(start_block=start_block, end_block=end_block)

        except HemeraBaseException as e:
            logger.error(f"An rpc response exception occurred while running {job.__class__.__name__}. error: {e}")
            if e.crashable:
                logger.error("Mission will crash immediately.")
                raise e

            if e.retriable:
                logger.debug(f"No: {retry} retry is about to start.")
            else:
                logger.error("Mission will not retry, and exit immediately.")
                raise e

        except Exception as e:
            logger.error(f"An unknown exception occurred while running {job.__class__.__name__}. error: {e}")
            raise e

    logger.debug(f"The number of retry is reached limit {max_retries}. Program will exit.")
    raise FastShutdownError(
        f"The {job} with parameters start_block:{start_block}, end_block:{end_block} "
        f"can't be automatically resumed after reached out limit of retries. Program will exit."
    )
