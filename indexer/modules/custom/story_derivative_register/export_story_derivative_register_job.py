import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_derivative_register.domain.story_register_derivative import StoryDerivativeRegister
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    StoryDerivativeRegistered,
    extract_derivative_registered,
    derivative_registered_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xf49da534215DA7b48E57A41d41dac25C912FCC60"]


def _filter_mint_tokens(logs: List[Log]) -> List[StoryDerivativeRegistered]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_derivative_registered(log)
    # return [transfer for transfer in token_transfers if
    #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
    print(token_transfers)
    return token_transfers


class ExportStoryLicenseRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryDerivativeRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            StoryDerivativeRegister(
                transaction_hash=StoryDerivativeRegistered.transaction_hash,
                caller=StoryDerivativeRegistered.caller,
                log_index = StoryDerivativeRegistered.log_index,
                child_ip_id=StoryDerivativeRegistered.child_ip_id,
                license_token_ids=StoryDerivativeRegistered.license_token_ids,
                parent_ip_ids=StoryDerivativeRegistered.parent_ip_ids,
                license_template = StoryDerivativeRegistered.license_template,
                license_terms_ids=StoryDerivativeRegistered.license_terms_ids,
                block_number=StoryDerivativeRegistered.block_number,
                block_timestamp = StoryDerivativeRegistered.block_timestamp
            ) for StoryDerivativeRegistered in mint_tokens
        ]
        print(erc721_mint_infos)
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[derivative_registered_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)