import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.filter_transaction_data_job import FilterTransactionDataJob
from indexer.modules.custom.erc721_token_mint.domain.erc721_mint_time import ERC721TokenMint
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    TokenTransfer,
    extract_transfer_from_log,
    transfer_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x10dde7d62819127deb817cde1174138af9bdb884"]


def _filter_mint_tokens(logs: List[Log]) -> List[TokenTransfer]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_transfer_from_log(log)
    return [transfer for transfer in token_transfers if
            transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]


class ExportERC721MintTimeJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [ERC721TokenMint]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            ERC721TokenMint(
                token_address=token.token_address,
                token_id=token.value,
                block_timestamp=token.block_timestamp,
                block_number=token.block_number,
                transaction_hash=token.transaction_hash
            ) for token in mint_tokens
        ]
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[transfer_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)
