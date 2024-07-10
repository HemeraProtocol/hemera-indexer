import logging
import os
import time
from datetime import timezone, datetime

from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import insert

from controller.base_controller import BaseController
from controller.dispatcher.base_dispatcher import BaseDispatcher
from exporters.jdbc.schema.sync_record import SyncRecord
from utils.exception_control import HemeraBaseException
from utils.file_utils import write_to_file, delete_file
from utils.web3_utils import build_web3


class StreamController(BaseController):

    def __init__(self,
                 service,
                 batch_web3_provider,
                 entity_types,
                 job_dispatcher=BaseDispatcher(),
                 max_retries=5):
        super().__init__(service)
        self.web3 = build_web3(batch_web3_provider)
        self.entity_types = entity_types
        self.job_dispatcher = job_dispatcher
        self.max_retries = max_retries

    def action(self,
               start_block=None,
               end_block=None,
               block_batch_size=10,
               period_seconds=10,
               retry_errors=True,
               pid_file=None):
        try:
            if pid_file is not None:
                logging.info('Creating pid file {}'.format(pid_file))
                write_to_file(pid_file, str(os.getpid()))

            self._do_stream(start_block, end_block, block_batch_size, retry_errors, period_seconds)

        finally:
            if pid_file is not None:
                logging.info('Deleting pid file {}'.format(pid_file))
                delete_file(pid_file)

    def _shutdown(self):
        pass

    def _do_stream(self, start_block, end_block, steps, retry_errors, period_seconds):
        last_synced_block = self._get_last_synced_block()
        if start_block is not None or last_synced_block == -1:
            last_synced_block = (start_block or 0) - 1

        tries, tries_reset = 0, True
        while True and (end_block is None or last_synced_block < end_block):
            synced_blocks = 0

            try:
                tries_reset = True
                current_block = self._get_current_block_number()

                target_block = self._calculate_target_block(current_block, last_synced_block, end_block, steps)
                synced_blocks = max(target_block - last_synced_block, 0)

                logging.info('Current block {}, target block {}, last synced block {}, blocks to sync {}'.format(
                    current_block, target_block, last_synced_block, synced_blocks))

                if synced_blocks != 0:
                    # ETL program's main logic
                    self.job_dispatcher.run(last_synced_block + 1, target_block)

                    logging.info('Writing last synced block {}'.format(target_block))
                    self._set_last_synced_block(target_block)
                    last_synced_block = target_block

            except HemeraBaseException as e:
                logging.exception(f'An rpc response exception occurred while syncing block data. error: {e}')
                if e.crashable:
                    logging.exception('Mission will crash immediately.')
                    raise e

                if e.retriable:
                    tries += 1
                    tries_reset = False
                    if tries >= self.max_retries:
                        logging.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                        raise e
                    else:
                        logging.info(f'No: {tries} retry is about to start.')
                else:
                    logging.exception('Mission will not retry, and exit immediately.')
                    raise e

            except Exception as e:
                logging.exception('An exception occurred while syncing block data.')
                tries += 1
                tries_reset = False
                if not retry_errors or tries >= self.max_retries:
                    logging.info(f"The number of retry is reached limit {self.max_retries}. Program will exit.")
                    raise e
                else:
                    logging.info(f'No: {tries} retry is about to start.')
            finally:
                if tries_reset:
                    tries = 0

            if synced_blocks <= 0:
                logging.info('Nothing to sync. Sleeping for {} seconds...'.format(period_seconds))
                time.sleep(period_seconds)

    def _get_current_block_number(self):
        return int(self.web3.eth.block_number)

    def _get_last_synced_block(self):
        session = self.db_service.get_service_session()
        try:
            result = session.query(SyncRecord.last_block_number).filter(
                and_(SyncRecord.mission_type == self.__class__.__name__,
                     SyncRecord.entity_types == self.entity_types)
            ).scalar()
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()
        if result is not None:
            return result
        return 0

    def _set_last_synced_block(self, last_synced_block):
        session = self.db_service.get_service_session()
        update_time = func.to_timestamp(int(datetime.now(timezone.utc).timestamp()))
        try:
            statement = insert(SyncRecord).values({
                "mission_type": self.__class__.__name__,
                "entity_types": self.entity_types,
                "last_block_number": last_synced_block,
                "update_time": update_time
            }).on_conflict_do_update(index_elements=[SyncRecord.mission_type, SyncRecord.entity_types],
                                     set_=
                                     {
                                         "last_block_number": last_synced_block,
                                         "update_time": update_time
                                     })

            session.execute(statement)
            session.commit()
        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

    @staticmethod
    def _calculate_target_block(current_block, last_synced_block, end_block, steps):
        target_block = min(current_block, last_synced_block + steps)
        target_block = min(target_block, end_block) if end_block is not None else target_block
        return target_block
