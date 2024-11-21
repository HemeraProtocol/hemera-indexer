import logging
import os
import time
from typing import List

from common.utils.exception_control import FastShutdownError, HemeraBaseException
from common.utils.file_utils import delete_file, write_to_file
from common.utils.web3_utils import build_web3
from indexer.controller.base_controller import BaseController
from indexer.executors.concurrent_job_executor import ConcurrentJobExecutor
from indexer.jobs.base_job import BaseJob
from indexer.utils.BufferService import BufferService
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.limit_reader import LimitReader
from indexer.utils.sync_recorder import BaseRecorder

# exception_recorder = ExceptionRecorder()

logger = logging.getLogger(__name__)

M_JOBS: int = int(os.environ.get("M_JOBS", 4))
M_TIMEOUT: int = int(os.environ.get("M_TIMEOUT", 100))
M_SIZE: int = int(os.environ.get("M_SIZE", 100))


class StreamController(BaseController):

    def __init__(
        self,
        batch_web3_provider,
        max_processors,
        sync_recorder: BaseRecorder,
        scheduled_jobs: List[BaseJob],
        item_exporters,
        required_output_types,
        limit_reader: LimitReader,
        max_retries=5,
        retry_from_record=False,
        delay=0,
        _manager=None,
    ):
        self.entity_types = 1
        self.web3 = build_web3(batch_web3_provider)
        self.required_output_types = [output.type() for output in required_output_types]
        self.buffer_service = BufferService(
            item_exporters, self.required_output_types, export_workers=max_processors, block_size=100
        )
        self.job_executor = (
            ConcurrentJobExecutor(buffer_service=self.buffer_service, max_processors=max_processors)
            if max_processors > 1
            else None
        )
        self.sync_recorder = sync_recorder
        self.scheduled_jobs = scheduled_jobs
        self.limit_reader = limit_reader
        self.max_retries = max_retries
        self.retry_from_record = retry_from_record
        self.delay = delay

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
                logger.info("Creating pid file {}".format(pid_file))
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
                    if self.job_executor:
                        self.job_executor.submit(
                            run_jobs,
                            jobs=self.scheduled_jobs,
                            start_block=last_synced_block + 1,
                            end_block=target_block,
                            max_retries=self.max_retries,
                        )
                    else:
                        export_data = run_jobs(
                            jobs=self.scheduled_jobs,
                            start_block=last_synced_block + 1,
                            end_block=target_block,
                            max_retries=self.max_retries,
                        )
                        self.buffer_service.write(export_data)

                    # logger.info("Writing last synced block {}".format(target_block))
                    # self.sync_recorder.set_last_synced_block(target_block)
                    last_synced_block = target_block

                if synced_blocks <= 0:
                    logger.info("Nothing to sync. Sleeping for {} seconds...".format(period_seconds))
                    time.sleep(period_seconds)

        finally:
            if pid_file is not None:
                logger.info("Deleting pid file {}".format(pid_file))
                delete_file(pid_file)

    def _shutdown(self):
        pass

    def split_blocks(self, start_block, end_block, step):
        blocks = []
        for i in range(start_block, end_block + 1, step):
            blocks.append((i, min(i + step - 1, end_block)))
        return blocks

    def _calculate_target_block(self, current_block, last_synced_block, end_block, steps):
        target_block = min(current_block - self.delay, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block


def run_jobs(jobs, start_block, end_block, max_retries, processor=None):
    try:
        jobs_export_data = {}
        for job in jobs:
            job_export_data = job_with_retires(
                job, start_block=start_block, end_block=end_block, max_retries=max_retries, processor=processor
            )
            jobs_export_data.update(job_export_data)
    except Exception as e:
        raise e

    return jobs_export_data


def job_with_retires(job, start_block, end_block, max_retries, processor=None):
    for retry in range(max_retries):
        try:
            return job.run(start_block=start_block, end_block=end_block, processor=processor)

        except HemeraBaseException as e:
            logger.error(f"An rpc response exception occurred while running {job.__class__.__name__}. error: {e}")
            if e.crashable:
                logger.error("Mission will crash immediately.")
                raise e

            if e.retriable:
                logger.info(f"No: {retry} retry is about to start.")
            else:
                logger.error("Mission will not retry, and exit immediately.")
                raise e

        except Exception as e:
            logger.error(f"An unknown exception occurred while running {job.__class__.__name__}. error: {e}")
            raise e

    logger.info(f"The number of retry is reached limit {max_retries}. Program will exit.")
    raise FastShutdownError(
        f"The {job} with parameters start_block:{start_block}, end_block:{end_block} "
        f"can't be automatically resumed after reached out limit of retries. Program will exit."
    )


def handle_success(processor: str, start_block: int, end_block: int):
    # self.sync_recorder.set_last_synced_block(target_block)
    pass


def handle_failure(processor: str, start_block: int, end_block: int):
    pass
