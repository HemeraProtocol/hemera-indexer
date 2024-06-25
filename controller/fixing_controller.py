import logging
import time
from datetime import timezone, datetime
from threading import Condition, Lock

from sqlalchemy import update, and_
from sqlalchemy.dialects.postgresql import insert

from controller.base_controller import BaseController
from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.fix_record import FixRecord
from jobs.fixing_block_consensus_job import FixingBlockConsensusJob
from utils.web3_utils import build_web3


class FixingController(BaseController):

    def __init__(self,
                 service,
                 batch_web3_provider,
                 batch_web3_debug_provider,
                 ranges):
        super().__init__(service)
        self.ranges = ranges
        self.web3 = build_web3(batch_web3_provider)
        self.fixing_job = FixingBlockConsensusJob(
            service=service,
            batch_web3_provider=batch_web3_provider,
            batch_web3_debug_provider=batch_web3_debug_provider)
        self.condition = Condition()
        self.waite_lock = Lock()
        self.waite_count = 0

    def action(self,
               block_number,
               retry_errors=True):
        job_id = self.submit_new_fixing_job(block_number, self.ranges)
        self.increment_waiting()
        with self.condition:
            # condition can lock other thread, using this check to prevent other process going through
            if not self.check_job_runnable(job_id):
                logging.info(
                    'Detected other process is fixing data, this process will shutdown immediately.\n'
                    'Fixing job has been submitted, it will auto running after other process complete their work.\n'
                    'Please do not re-run this process manually, it will occur some unexpected problem. ')
                # wake up other thread in same process, they will also shut down immediately after submit.
                self.condition.notify_all()
                exit(1)

            self.decrement_waiting()
            self.update_job_info(job_id, {"job_status": "running"})

            for i in range(self.ranges):
                try:
                    fix_need = self.check_block_need_fix(block_number - i)
                    if fix_need:
                        logging.info(f'Fixing block No.{block_number - i}')
                        self._do_fixing(block_number - i, retry_errors)
                    else:
                        logging.info(f'Block No.{block_number - i} is verified to be correct. Skip to the next one.')

                finally:
                    if fix_need and i == self.ranges - 1:
                        self.ranges += 1
                    # submit the progress to db
                    self.update_job_info(job_id,
                                         job_info={
                                             "last_fixed_block_number": block_number - i,
                                             "remain_process": self.ranges - i - 1,
                                             "update_time": datetime.now(timezone.utc),
                                             "job_status": "interrupt"
                                         })

            self.update_job_info(job_id, {"job_status": "completed"})
            self.wake_up_next_job()

            logging.info('Fixing mission completed.')

    def _do_fixing(self, fix_block, retry_errors=True):
        while True:
            synced_blocks = 0

            try:
                logging.info(f'Fixing block {fix_block}')

                if synced_blocks != 0:
                    # set block number first
                    self.fixing_job.set_fix_block_number(fix_block)

                    # Main fixing logic
                    self.fixing_job.run()

                    logging.info(f'Block No.{fix_block} and relative entities completely fixed .')

            except Exception as e:
                logging.exception('An exception occurred while fixing block data.')
                if not retry_errors:
                    raise e
                else:
                    logging.info('After 5 seconds will retry the job.')
                    time.sleep(5)

    def increment_waiting(self):
        with self.waite_lock:
            self.waite_count += 1

    def decrement_waiting(self):
        with self.waite_lock:
            self.waite_count -= 1

    def get_waiting_count(self):
        with self.waite_lock:
            return self.waite_count

    def submit_new_fixing_job(self, start_block_number, remain_process):
        session = self.db_service.get_service_session()
        stmt = insert(FixRecord).values(
            {
                "start_block_number": start_block_number,
                "last_fixed_block_number": start_block_number + 1,
                "remain_process": remain_process,
                "job_status": "submitted"
            })
        try:
            result = session.execute(stmt)
            session.commit()
        finally:
            session.close()

        return result.inserted_primary_key[0]

    def update_job_info(self, job_id, job_info):
        session = self.db_service.get_service_session()
        try:
            stmt = (
                update(FixRecord)
                .where(FixRecord.job_id == job_id)
                .values(job_info))
            result = session.execute(stmt)
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
        if self.get_waiting_count() > 0:
            self.condition.notify_all()
            return

        session = self.db_service.get_service_session()
        job = (session.query(FixRecord)
               .filter(FixRecord.job_status != "completed")
               .order_by(FixRecord.create_time)
               .first())

        if job:
            self.action(job.last_fixed_block_number - 1, job.remain_process)

    def check_block_need_fix(self, block_number):
        block = self.web3.eth.get_block(block_number)
        block_hash = block.hash.hex()

        session = self.db_service.get_service_session()
        result = (session.query(Blocks)
                  .filter(and_(Blocks.number == block_number, Blocks.hash == bytes.fromhex(block_hash[2:])))
                  .first())

        return result is None
