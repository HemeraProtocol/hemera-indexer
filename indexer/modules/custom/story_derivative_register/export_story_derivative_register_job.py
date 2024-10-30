import logging
from typing import List
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_derivative_register.domains.story_register_derivative import StoryDerivativeRegister, StoryDerivativeRegistered
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.modules.custom.story_derivative_register.register_derivative_abi import DERIVATIVE_REGISTERED_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xd81fd78f557b457b4350cB95D20b547bFEb4D857","0xf49da534215DA7b48E57A41d41dac25C912FCC60"]

def handle_derivative_registered_event(log: Log) -> List[StoryDerivativeRegistered]:
    decode_data = DERIVATIVE_REGISTERED_EVENT.decode_log(log)

    caller = decode_data.get("caller")
    child_ip_id = decode_data.get("childIpId")
    license_token_ids = decode_data.get("licenseTokenIds")
    parent_ip_ids = decode_data.get("parentIpIds")
    license_terms_ids = decode_data.get("licenseTermsIds")
    license_template = decode_data.get("licenseTemplate")
    return [
        StoryDerivativeRegistered(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            caller=caller,
            child_ip_id=child_ip_id,
            license_token_ids=license_token_ids,
            parent_ip_ids=parent_ip_ids,
            license_terms_ids = license_terms_ids,
            license_template = license_template,
			contract_address = log.address,
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]


def _filter_derivative_register(logs: List[Log]) -> List[StoryDerivativeRegistered]:
    story_data = []
    for log in logs:
        if log.topic0 == DERIVATIVE_REGISTERED_EVENT.get_signature():
            story_data += handle_derivative_registered_event(log)

    return story_data


class ExportStoryDerivativeRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryDerivativeRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        derivative_register = _filter_derivative_register(logs)

        story_derivative_registered = [
            StoryDerivativeRegister(
                caller=StoryDerivativeRegistered.caller,
                log_index = StoryDerivativeRegistered.log_index,
                child_ip_id=StoryDerivativeRegistered.child_ip_id,
                license_token_ids=StoryDerivativeRegistered.license_token_ids,
                parent_ip_ids=StoryDerivativeRegistered.parent_ip_ids,
                license_template = StoryDerivativeRegistered.license_template,
                license_terms_ids=StoryDerivativeRegistered.license_terms_ids,
                contract_address = StoryDerivativeRegistered.contract_address,
                transaction_hash=StoryDerivativeRegistered.transaction_hash,
                block_number=StoryDerivativeRegistered.block_number,
                block_timestamp = StoryDerivativeRegistered.block_timestamp
            ) for StoryDerivativeRegistered in derivative_register
        ]
        self._collect_domains(story_derivative_registered)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[DERIVATIVE_REGISTERED_EVENT.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)