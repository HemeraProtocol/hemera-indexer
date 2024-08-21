import logging
import os
import time

from common.utils.exception_control import HemeraBaseException
from common.utils.file_utils import delete_file, write_to_file
from common.utils.web3_utils import build_web3
from indexer.controller.base_controller import BaseController
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.sync_recorder import BaseRecorder

exception_recorder = ExceptionRecorder()


class StreamController(BaseController):

    def __init__(
        self,
        batch_web3_provider,
        sync_recorder: BaseRecorder,
        job_scheduler: JobScheduler,
        max_retries=5,
        retry_from_record=False,
    ):
        self.entity_types = 1
        self.sync_recorder = sync_recorder
        self.web3 = build_web3(batch_web3_provider)
        self.job_scheduler = job_scheduler
        self.max_retries = max_retries
        self.retry_from_record = retry_from_record

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
                logging.info("Creating pid file {}".format(pid_file))
                write_to_file(pid_file, str(os.getpid()))

            self._do_stream(start_block, end_block, block_batch_size, retry_errors, period_seconds)

        finally:
            if pid_file is not None:
                logging.info("Deleting pid file {}".format(pid_file))
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
                current_block = self._get_current_block_number()

                target_block = self._calculate_target_block(current_block, last_synced_block, end_block, steps)
                synced_blocks = max(target_block - last_synced_block, 0)

                logging.info(
                    "Current block {}, target block {}, last synced block {}, blocks to sync {}".format(
                        current_block, target_block, last_synced_block, synced_blocks
                    )
                )

                if synced_blocks != 0:
                    # ETL program's main logic
                    self.job_scheduler.run_jobs(last_synced_block + 1, target_block)

                    logging.info("Writing last synced block {}".format(target_block))
                    self.sync_recorder.set_last_synced_block(target_block)
                    last_synced_block = target_block

            except HemeraBaseException as e:
                logging.exception(f"An rpc response exception occurred while syncing block data. error: {e}")
                if e.crashable:
                    logging.exception("Mission will crash immediately.")
                    raise e

                if e.retriable:
                    tries += 1
                    tries_reset = False
                    if tries >= self.max_retries:
                        logging.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                        raise e
                    else:
                        logging.info(f"No: {tries} retry is about to start.")
                else:
                    logging.exception("Mission will not retry, and exit immediately.")
                    raise e

            except Exception as e:
                logging.exception("An exception occurred while syncing block data.")
                tries += 1
                tries_reset = False
                if not retry_errors or tries >= self.max_retries:
                    logging.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                    exception_recorder.force_to_flush()
                    raise e

                else:
                    logging.info(f"No: {tries} retry is about to start.")
            finally:
                if tries_reset:
                    tries = 0

            if synced_blocks <= 0:
                logging.info("Nothing to sync. Sleeping for {} seconds...".format(period_seconds))
                time.sleep(period_seconds)

    def _get_current_block_number(self):
        return int(self.web3.eth.block_number)

    @staticmethod
    def _calculate_target_block(current_block, last_synced_block, end_block, steps):
        target_block = min(current_block, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block
