import logging
from typing import List
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_attach.domains.story_attach_license import StoryLicenseAttach, StoryLicenseTermsAttach
from indexer.modules.custom.story_license_attach.license_attach_abi import LICENSE_ATTACH_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera.util import calculate_execution_time

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xd81fd78f557b457b4350cB95D20b547bFEb4D857", "0xf49da534215DA7b48E57A41d41dac25C912FCC60"]

def handle_license_attach_event(log: Log) -> List[StoryLicenseTermsAttach]:
    decode_data = LICENSE_ATTACH_EVENT.decode_log_ignore_indexed(log)

    caller = decode_data.get("caller").lower()
    ip_id = decode_data.get("ipId")
    license_template = decode_data.get("licenseTemplate").lower()
    license_terms_id = decode_data.get("licenseTermsId")

    return [
        StoryLicenseTermsAttach(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            caller=caller,
            ip_id=ip_id,
            license_template=license_template,
            license_terms_id=license_terms_id,
			contract_address=log.address,
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]

def _filter_license_attach(logs: List[Log]) -> List[StoryLicenseTermsAttach]:
    story_data = []
    for log in logs:
        if log.topic0 == LICENSE_ATTACH_EVENT.get_signature():
            story_data += handle_license_attach_event(log)

    return story_data


class ExportStoryLicenseAttachJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryLicenseAttach]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        license_attach = _filter_license_attach(logs)

        story_license_attached = [
            StoryLicenseAttach(
                caller=StoryLicenseTermsAttach.caller,
                log_index=StoryLicenseTermsAttach.log_index,
                ip_id=StoryLicenseTermsAttach.ip_id,
                license_template=StoryLicenseTermsAttach.license_template,
                license_terms_id=StoryLicenseTermsAttach.license_terms_id,
                block_number=StoryLicenseTermsAttach.block_number,
                contract_address=StoryLicenseTermsAttach.contract_address,
                transaction_hash=StoryLicenseTermsAttach.transaction_hash,
            )
            for StoryLicenseTermsAttach in license_attach
        ]
        self._collect_domains(story_license_attached)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(addresses=TARGET_TOKEN_ADDRESS, topics=[LICENSE_ATTACH_EVENT.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)
