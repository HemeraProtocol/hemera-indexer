import logging
import subprocess
from typing import Union

from sqlalchemy import and_

from hemera.common.models.blocks import Blocks
from hemera.common.utils.format_utils import as_dict
from hemera.indexer.domain import dict_to_dataclass
from hemera.indexer.domain.block import Block
from hemera.indexer.jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class CheckBlockConsensusJob(BaseJob):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = kwargs["config"]
        self._batch_web3_debug_provider = kwargs["batch_web3_debug_provider"]
        self._batch_size = kwargs["batch_size"]
        self._multicall = kwargs["multicall"]
        self._debug_batch_size = kwargs["debug_batch_size"]
        self.db_service = self._config.get("db_service") if "db_service" in self._config else None
        self._postgre_uri = self.db_service.get_service_uri() if self.db_service else None

        self.last_batch_end_block = None
        self.check_switch = self._config.get("db_service", None) is not None

    def _process(self, **kwargs):
        if not self.check_switch:
            return

        batch_blocks = self._data_buff[Block.type()]

        if self.last_batch_end_block:
            batch_blocks = [self.last_batch_end_block] + batch_blocks
        else:
            last_block = self._query_last_block(batch_blocks[0])
            if last_block:
                batch_blocks = [last_block] + batch_blocks

        batch_blocks.reverse()
        parent_hash = batch_blocks[0].parent_hash
        for block in batch_blocks[1:]:
            block_hash = block.hash
            if block_hash != parent_hash:
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
                    "-m",
                    f"{self._multicall}",
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

    def _query_last_block(self, block: Block) -> Union[Block, None]:
        if block is None:
            return None

        check_block_number = block.number - 1

        session = self.db_service.get_service_session()
        try:
            result = session.query(Blocks).filter(and_(Blocks.number == check_block_number)).first()
        finally:
            session.close()

        block = dict_to_dataclass(as_dict(result), Block) if result else None
        return block
