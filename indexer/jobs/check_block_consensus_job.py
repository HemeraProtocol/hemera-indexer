import logging
import threading
from multiprocessing import Process

from indexer.controller.reorg_controller import FixingController
from indexer.domain.block import Block
from indexer.jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class CheckBlockConsensusJob(BaseJob):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_batch_end_block = None
        config = kwargs['config']
        self.check_switch = config.get('db_service', None) is not None
        if self.check_switch:
            self.fix_controller = FixingController(service=config.get('db_service'),
                                                   batch_web3_provider=kwargs['batch_web3_provider'],
                                                   batch_web3_debug_provider=kwargs['batch_web3_debug_provider'],
                                                   ranges=1000,
                                                   batch_size=kwargs['batch_size'],
                                                   debug_batch_size=kwargs['debug_batch_size'])

    def _process(self):
        if not self.check_switch:
            return

        batch_blocks = self._data_buff[Block.type()]

        if self.last_batch_end_block is not None:
            batch_blocks = [self.last_batch_end_block] + batch_blocks

        batch_blocks.reverse()
        parent_hash = batch_blocks[0]['parent_hash']
        for block in batch_blocks[1:]:
            block_hash = block['hash']
            if block_hash != parent_hash:
                # non-consensus detected
                fixing_thread = Process(target=self.fix_controller.action,
                                        kwargs={'block_number': block['number']})
                fixing_thread.start()
                break

            parent_hash = block['parent_hash']

        self.last_batch_end_block = batch_blocks[-1]
