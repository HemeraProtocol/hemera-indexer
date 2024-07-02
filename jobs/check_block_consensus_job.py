import logging
import threading

from controller.fixing_controller import FixingController
from jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class CheckBlockConsensusJob(BaseJob):
    def __init__(self,
                 entity_types,
                 service,
                 batch_web3_provider,
                 batch_web3_debug_provider,
                 ranges,
                 batch_size,
                 debug_batch_size):
        super().__init__(entity_types=entity_types)
        self.last_batch_end_block = None
        self.fix_controller = FixingController(service=service,
                                               batch_web3_provider=batch_web3_provider,
                                               batch_web3_debug_provider=batch_web3_debug_provider,
                                               ranges=ranges,
                                               batch_size=batch_size,
                                               debug_batch_size=debug_batch_size)

    def _process(self):

        if self._entity_types & 255 == 255:
            batch_blocks = self._data_buff['formated_block']

            if self.last_batch_end_block is not None:
                batch_blocks = [self.last_batch_end_block] + batch_blocks

            batch_blocks.reverse()
            parent_hash = batch_blocks[0]['parent_hash']
            for block in batch_blocks[1:]:
                block_hash = block['hash']
                if block_hash != parent_hash:
                    # non-consensus detected
                    fixing_thread = threading.Thread(target=self.fix_controller.action,
                                                     kwargs={'block_number': block['number']})
                    fixing_thread.start()
                    break

                parent_hash = block['parent_hash']

            self.last_batch_end_block = batch_blocks[-1]

        self._data_buff = dict()
