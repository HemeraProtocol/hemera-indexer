import logging
from typing import List

from common.utils.web3_utils import ZERO_ADDRESS

# Dependency dataclass
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer, extract_transfer_from_log
from indexer.jobs.base_job import FilterTransactionDataJob

# Custom dataclass
from indexer.modules.custom.erc721_token_mint.domain.erc721_mint_time import ERC721TokenMint
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

# Utility
from indexer.utils.abi_setting import ERC721_TRANSFER_EVENT

logger = logging.getLogger(__name__)


def _filter_mint_tokens(logs: List[Log]) -> List[TokenTransfer]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_transfer_from_log(log)
    return [
        transfer
        for transfer in token_transfers
        if transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"
    ]


class DemoJob(FilterTransactionDataJob):
    # Declare existing dataclass you may need for your job
    # The indexer will automatically run other jobs and prepare the dataclass
    dependency_types = [Log]

    # This is to declare output dataclass your job outputs
    # This is helpful if you write other job which depends on these dataclasses
    output_types = [ERC721TokenMint]

    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._contract_list = self.user_defined_config.get("contract_address")
        self.logger.info("Contracts to process %s", self._contract_list)

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(addresses=self._contract_list, topics=[ERC721_TRANSFER_EVENT.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        # This is how you get your dependency dataclass indexer prepared for you
        # Note that filter will apply
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
