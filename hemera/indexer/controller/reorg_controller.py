import logging
import time
from datetime import datetime, timezone

from sqlalchemy import and_, update
from sqlalchemy.dialects.postgresql import insert

from hemera.common.models.blocks import Blocks
from hemera.common.models.fix_record import FixRecord
from hemera.common.utils.exception_control import HemeraBaseException
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.common.utils.web3_utils import build_web3
from hemera.indexer.controller.base_controller import BaseController
from hemera.indexer.utils.exception_recorder import ExceptionRecorder

exception_recorder = ExceptionRecorder()


class ReorgController(BaseController):

    def __init__(self, batch_web3_provider, job_scheduler, ranges, config, max_retries=5):
        self.ranges = ranges
        self.web3 = build_web3(batch_web3_provider)
        self.db_service = config.get("db_service")
        self.job_scheduler = job_scheduler
        self.max_retries = max_retries

    def action(self, job_id=None, block_number=None, remains=None, retry_errors=True):
        if block_number is None:
            raise ValueError("Reorging mission must provide a block_number.")
        if remains is None:
            remains = self.ranges

        if job_id is None:
            job_id = self.submit_new_fixing_job(block_number, remains)

        # condition can lock other thread, using this check to prevent other process going through
        if not self.check_job_runnable(job_id):
            logging.info(
                "Detected other process is reorging data, this process will shutdown immediately.\n"
                "Reorging job has been submitted, it will auto running after other process complete their work.\n"
                "Please do not re-run this process manually, it will occur some unexpected problem. "
            )
            # wake up other thread in same process, they will also shut down immediately after submit.

            exit(1)

        self.update_job_info(job_id, {"job_status": "running"})

        offset, limit = 0, remains
        try:
            while offset < limit:
                fix_need = self.check_block_been_synced(block_number - offset) and self.check_block_need_fix(
                    block_number - offset
                )

                if fix_need:
                    logging.info(f"Reorging block No.{block_number - offset}")
                    self._do_fixing(block_number - offset, retry_errors)
                else:
                    logging.info(
                        f"Block No.{block_number - offset} is verified to be correct or has not been synced. "
                        f"Skip to the next one."
                    )

                if fix_need and offset == limit - 1:
                    offset += 1

                self.update_job_info(
                    job_id,
                    job_info={
                        "last_fixed_block_number": block_number - offset,
                        "remain_process": limit - offset - 1,
                        "update_time": datetime.now(timezone.utc),
                    },
                )
                offset += 1
        except (Exception, KeyboardInterrupt, HemeraBaseException) as e:
            self.update_job_info(
                job_id,
                job_info={
                    "last_fixed_block_number": block_number - offset + 1,
                    "remain_process": limit - offset,
                    "update_time": datetime.now(timezone.utc),
                    "job_status": "interrupt",
                },
            )
            logging.error(f"Reorging mission catch exception: {e}")
            raise e

        self.update_job_info(job_id, job_info={"job_status": "completed"})

        logging.info(f"Reorging mission start from block No.{block_number} and ranges {remains} has been completed.")

    def _do_fixing(self, fix_block, retry_errors=True):
        tries, tries_reset = 0, True
        while True:
            try:
                # Main reorging logic
                tries_reset = True
                self.job_scheduler.run_jobs(fix_block, fix_block)

                logging.info(f"Block No.{fix_block} and relative entities completely fixed .")
                break

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
                print(e)
                logging.exception("An exception occurred while reorging block data.")
                tries += 1
                tries_reset = False
                if not retry_errors or tries >= self.max_retries:
                    logging.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                    exception_recorder.force_to_flush()
                    raise e
                else:
                    logging.info("After 5 seconds will retry the job.")
                    time.sleep(5)

            finally:
                if tries_reset:
                    tries = 0

    def submit_new_fixing_job(self, start_block_number, remain_process):
        session = self.db_service.get_service_session()
        stmt = insert(FixRecord).values(
            {
                "start_block_number": start_block_number,
                "last_fixed_block_number": start_block_number + 1,
                "remain_process": remain_process,
                "job_status": "submitted",
            }
        )
        try:
            result = session.execute(stmt)
            session.commit()
        finally:
            session.close()

        return result.inserted_primary_key[0]

    def update_job_info(self, job_id, job_info):
        session = self.db_service.get_service_session()
        try:
            stmt = update(FixRecord).where(FixRecord.job_id == job_id).values(job_info)
            session.execute(stmt)
            session.commit()
        finally:
            session.close()

    def check_job_runnable(self, job_id):
        runnable = False
        session = self.db_service.get_service_session()
        try:
            running_cnt = session.query(FixRecord).filter(FixRecord.job_status == "running").count()
            runnable = running_cnt == 0
            if not runnable:
                running_job = session.query(FixRecord).filter(FixRecord.job_status == "running").first()
                runnable = running_job.job_id == job_id
        finally:
            session.close()
        return runnable

    def wake_up_next_job(self):
        session = self.db_service.get_service_session()
        job = None
        try:
            job = (
                session.query(FixRecord)
                .filter(FixRecord.job_status != "completed")
                .order_by(FixRecord.create_time)
                .first()
            )
        except Exception as e:
            logging.error(f"Wake up uncompleted job error: {e}.")
            raise e
        finally:
            session.close()

        return job

    def check_block_been_synced(self, block_number):
        session = self.db_service.get_service_session()
        try:
            result = session.query(Blocks).filter(and_(Blocks.number == block_number)).first()
        finally:
            session.close()
        return result is not None

    def check_block_need_fix(self, block_number):
        block = self.web3.eth.get_block(block_number)
        block_hash = block.hash.hex()

        session = self.db_service.get_service_session()
        try:
            result = (
                session.query(Blocks)
                .filter(
                    and_(
                        Blocks.number == block_number,
                        Blocks.hash == hex_str_to_bytes(block_hash),
                        Blocks.reorg == False,
                    )
                )
                .first()
            )
        finally:
            session.close()
        return result is None
