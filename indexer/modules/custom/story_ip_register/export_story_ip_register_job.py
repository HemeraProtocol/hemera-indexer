import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_ip_register.domains.story_register_ip import StoryIpRegister
from indexer.modules.custom.story_ip_register.ip_register_abi import (
    StoryIpRegistered,
    extract_ip_register,
    ip_register_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x1a9d0d28a0422F26D31Be72Edc6f13ea4371E11B", "0xe34A78B3d658aF7ad69Ff1EFF9012ECa025a14Be"]


def _filter_ip_register(logs: List[Log]) -> List[StoryIpRegistered]:
    story_data = []
    for log in logs:
        story_data += extract_ip_register(log)
    return story_data


class ExportStoryIpRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryIpRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        ip_register = _filter_ip_register(logs)

        story_ip_registers = [
            StoryIpRegister(
                ip_account=StoryIpRegistered.ip_account,
                nft_contract=StoryIpRegistered.token_contract,
                nft_id=StoryIpRegistered.token_id,
                chain_id=StoryIpRegistered.chain_id,
                block_number=StoryIpRegistered.block_number,
                contract_address=StoryIpRegistered.contract_address,
                transaction_hash=StoryIpRegistered.transaction_hash,
            )
            for StoryIpRegistered in ip_register
        ]
        self._collect_domains(story_ip_registers)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(addresses=TARGET_TOKEN_ADDRESS, topics=[ip_register_event.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)
