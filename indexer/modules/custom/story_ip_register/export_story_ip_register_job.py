import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_ip_register.domain.story_register_ip import StoryIpRegister
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    StoryIpRegistered,
    extract_ip_register,
    ip_register_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x1a9d0d28a0422F26D31Be72Edc6f13ea4371E11B"]

def _filter_mint_tokens(logs: List[Log]) -> List[StoryIpRegistered]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_ip_register(log)
    # return [transfer for transfer in token_transfers if
    #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
    # print(token_transfers)
    return token_transfers


class ExportStoryIpRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryIpRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            StoryIpRegister(
                ip_account=StoryIpRegistered.ip_account,
                nft_contract=StoryIpRegistered.token_contract,
                nft_id=StoryIpRegistered.token_id,
                chain_id=StoryIpRegistered.chain_id,
                block_number=StoryIpRegistered.block_number,
                transaction_hash=StoryIpRegistered.transaction_hash
            ) for StoryIpRegistered in mint_tokens
        ]
        print(erc721_mint_infos)
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[ip_register_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)
