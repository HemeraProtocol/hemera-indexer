import logging
from typing import List
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_ip_register.domains.story_register_ip import StoryIpRegister, StoryIpRegistered
from indexer.modules.custom.story_ip_register.ip_register_abi import IP_REGISTER_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera.util import calculate_execution_time

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x1a9d0d28a0422F26D31Be72Edc6f13ea4371E11B", "0xe34A78B3d658aF7ad69Ff1EFF9012ECa025a14Be"]


def handle_ip_register_event(log: Log) -> List[StoryIpRegistered]:
    decode_data = IP_REGISTER_EVENT.decode_log_ignore_indexed(log)

    account = decode_data.get("account").lower()
    #imp_address = decode_data.get("implementation").lower()
    chain_id = decode_data.get("chainId")
    token_contract = decode_data.get("tokenContract").lower()
    token_id = decode_data.get("tokenId")

    return [
        StoryIpRegistered(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            ip_account=account,
            chain_id=chain_id,
            token_contract=token_contract,
            token_id=token_id,
            contract_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def _filter_ip_register(logs: List[Log]) -> List[StoryIpRegistered]:
    story_data = []
    for log in logs:
        if log.topic0 == IP_REGISTER_EVENT.get_signature():
            story_data += handle_ip_register_event(log)

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
            TopicSpecification(addresses=TARGET_TOKEN_ADDRESS, topics=[IP_REGISTER_EVENT.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)
