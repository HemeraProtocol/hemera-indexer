import logging
import subprocess

from indexer.domain.block import Block
from indexer.jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class CheckBlockConsensusJob(BaseJob):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = kwargs["config"]
        self._batch_web3_debug_provider = kwargs["batch_web3_debug_provider"]
        self._batch_size = kwargs["batch_size"]
        self._debug_batch_size = kwargs["debug_batch_size"]
        self._postgre_uri = self._config.get("db_service").get_service_uri() if "db_service" in self._config else None

        self.last_batch_end_block = None
        self.check_switch = self._config.get("db_service", None) is not None

    def _process(self, **kwargs):
        if not self.check_switch:
            return

        batch_blocks = self._data_buff[Block.type()]

        if self.last_batch_end_block is not None:
            batch_blocks = [self.last_batch_end_block] + batch_blocks

        batch_blocks.reverse()
        parent_hash = batch_blocks[0].parent_hash
        for block in batch_blocks[1:]:
            block_hash = block.hash
            if block_hash != parent_hash or block_hash[-1] == "0":
                # non-consensus detected
                ranges = max(len(batch_blocks), 5)
                command = [
                    "python",
                    "hemera.py",
                    "reorg",
                    "-p",
                    self._batch_web3_provider.endpoint_uri,
                    "-d",
                    self._batch_web3_debug_provider.endpoint_uri,
                    "-b",
                    f"{self._batch_size}",
                    "--debug-batch-size",
                    f"{self._debug_batch_size}",
                    "-pg",
                    self._postgre_uri,
                    "--block-number",
                    f"{block.number}",
                    "--ranges",
                    f"{ranges}",
                    "--log-file",
                    f"./logs/auto_reorg_{block.number}_{ranges}.log",
                ]
                subprocess.Popen(command, start_new_session=True)
                self.logger.info(f"Reorg process started with command: {command}")
                break

            parent_hash = block.parent_hash

        self.last_batch_end_block = batch_blocks[0]
