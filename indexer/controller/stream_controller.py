import logging
import os
import time

from common.utils.exception_control import FastShutdownError, HemeraBaseException
from common.utils.file_utils import delete_file, write_to_file
from common.utils.web3_utils import build_web3
from indexer.controller.base_controller import BaseController
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.limit_reader import LimitReader
from indexer.utils.record_report import RecordReporter
from indexer.utils.sync_recorder import BaseRecorder

exception_recorder = ExceptionRecorder()

logger = logging.getLogger(__name__)


class StreamController(BaseController):

    def __init__(
        self,
        batch_web3_provider,
        sync_recorder: BaseRecorder,
        job_scheduler: JobScheduler,
        limit_reader: LimitReader,
        max_retries=5,
        retry_from_record=False,
        delay=0,
        record_reporter=None,
    ):
        self.entity_types = 1
        self.sync_recorder = sync_recorder
        self.web3 = build_web3(batch_web3_provider)
        self.job_scheduler = job_scheduler
        self.limit_reader = limit_reader
        self.max_retries = max_retries
        self.retry_from_record = retry_from_record
        self.delay = delay
        self.chain_id = self._get_current_chain_id()
        self.record_reporter: RecordReporter = record_reporter
        if self.record_reporter is None:
            logger.warning(
                "RecordReporter not initialized, indexed records will not be reported to contract. "
                "The possible reason is that --report-private-key or --report-from-address are not set."
            )

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

            self._do_stream(start_block, end_block, block_batch_size, retry_errors, period_seconds)

        finally:
            if pid_file is not None:
                logger.info("Deleting pid file {}".format(pid_file))
                delete_file(pid_file)

    def _shutdown(self):
        pass

    def _do_stream(self, start_block, end_block, steps, retry_errors, period_seconds):
        last_synced_block = self.sync_recorder.get_last_synced_block()
        if start_block is not None:
            if (
                not self.retry_from_record
                or last_synced_block < start_block
                or (end_block is not None and last_synced_block > end_block)
            ):
                last_synced_block = start_block - 1

        tries, tries_reset = 0, True
        while True and (end_block is None or last_synced_block < end_block):
            synced_blocks = 0

            try:
                tries_reset = True
                current_block = self.limit_reader.get_current_block_number()
                if current_block is None:
                    raise FastShutdownError(
                        "Can't get current limit block number from limit reader."
                        "If you're using PGLimitReader, please confirm blocks table has one record at least."
                    )

                target_block = self._calculate_target_block(current_block, last_synced_block, end_block, steps)
                synced_blocks = max(target_block - last_synced_block, 0)

                logger.info(
                    "Current block {}, target block {}, last synced block {}, blocks to sync {}".format(
                        current_block, target_block, last_synced_block, synced_blocks
                    )
                )

                if synced_blocks != 0:
                    # ETL program's main logic
                    report_info = self.job_scheduler.run_jobs(last_synced_block + 1, target_block)
                    logger.info("Writing last synced block {}".format(target_block))
                    self.sync_recorder.set_last_synced_block(target_block)
                    if self.record_reporter:
                        self.record_reporter.report(self.chain_id, last_synced_block + 1, target_block, report_info)
                    last_synced_block = target_block

            except HemeraBaseException as e:
                logger.error(f"An rpc response exception occurred while syncing block data. error: {e}")
                if e.crashable:
                    logger.error("Mission will crash immediately.")
                    raise e

                if e.retriable:
                    tries += 1
                    tries_reset = False
                    if tries >= self.max_retries:
                        logger.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                        raise e
                    else:
                        logger.info(f"No: {tries} retry is about to start.")
                else:
                    logger.error("Mission will not retry, and exit immediately.")
                    raise e

            except Exception as e:
                logger.error("An exception occurred while syncing block data.")
                tries += 1
                tries_reset = False
                if not retry_errors or tries >= self.max_retries:
                    logger.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                    exception_recorder.force_to_flush()
                    raise e

                else:
                    logger.info(f"No: {tries} retry is about to start.")
            finally:
                if tries_reset:
                    tries = 0

            if synced_blocks <= 0:
                logger.info("Nothing to sync. Sleeping for {} seconds...".format(period_seconds))
                time.sleep(period_seconds)

    def _get_current_block_number(self):
        return int(self.web3.eth.block_number)

    def _get_current_chain_id(self):
        return self.web3.eth.chain_id

    def _calculate_target_block(self, current_block, last_synced_block, end_block, steps):
        target_block = min(current_block - self.delay, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block
