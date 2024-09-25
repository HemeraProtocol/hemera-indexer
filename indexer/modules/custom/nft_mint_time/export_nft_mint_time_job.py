import logging
from typing import List

from indexer.domain.log import Log
from indexer.jobs.base_job import BaseExportJob
from indexer.modules.custom.erc721_mint_time.domain.erc721_mint_time import ERC721TokenMint
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    ERC721TokenTransfer,
    TokenTransfer,
    extract_transfer_from_log,
)

logger = logging.getLogger(__name__)

 # Constants
TARGET_TOKEN_ADDRESS = ["0x10dde7d62819127deb817cde1174138af9bdb884"]


class ExportERC721MintTimeJob(BaseExportJob):
    dependency_types = [Log]
    output_types = [ERC721TokenMint]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = self._filter_mint_tokens(logs)
        
        for token in mint_tokens:
            erc721_mint_time = ERC721TokenMint(
                token_address=token.token_address,
                token_id=token.value,
                block_timestamp=token.block_timestamp,
                block_number=token.block_number,
                transaction_hash=token.transaction_hash,
            )
            self._collect_domain(erc721_mint_time)

    def _filter_mint_tokens(self, logs: List[Log]) -> List[TokenTransfer]:
        tokenTransfers = []
        for log in logs:
            tokenTransfers += extract_transfer_from_log(log)
        return [transfer for transfer in tokenTransfers if transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]

    
    def _process(self, **kwargs):
        pass
