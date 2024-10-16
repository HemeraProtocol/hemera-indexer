import logging
from typing import List

from common.utils.web3_utils import ZERO_ADDRESS

# Dependency dataclass
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer, extract_transfer_from_log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob

# Custom dataclass
from indexer.modules.custom.erc721_token_mint.domain.erc721_mint_time import ERC721TokenMint
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

# Utility
from indexer.utils.abi_setting import ERC721_TRANSFER_EVENT

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x144e8e2450d8660c6de415a56452b10187343ad6"]


def _filter_mint_tokens(logs: List[Log]) -> List[TokenTransfer]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_transfer_from_log(log)
    return [
        transfer
        for transfer in token_transfers
        if transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"
    ]


class ExportERC721MintTimeJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [ERC721TokenMint]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(addresses=TARGET_TOKEN_ADDRESS, topics=[ERC721_TRANSFER_EVENT.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        # Get filter log from
        logs = self._data_buff[Log.type()]

        # Core logic of UDF
        mint_tokens = _filter_mint_tokens(logs)
        erc721_mint_infos = [
            ERC721TokenMint(
                token_address=token.token_address,
                token_id=token.value,
                block_timestamp=token.block_timestamp,
                block_number=token.block_number,
                transaction_hash=token.transaction_hash,
            )
            for token in mint_tokens
        ]

        # This is one of the functions that convert dataclass into models and export
        # The other functions can be found in indexer/jobs/base_job.py
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass
