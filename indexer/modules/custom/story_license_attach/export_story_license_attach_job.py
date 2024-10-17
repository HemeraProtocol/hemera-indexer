import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_attach.domains.story_attach_license import StoryLicenseAttach
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.modules.custom.story_license_attach.domains.license_attach_abi import (
    StoryLicenseTermsAttach,
    extract_license_attach,
    license_attach_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xd81fd78f557b457b4350cB95D20b547bFEb4D857"]


def _filter_license_attach(logs: List[Log]) -> List[StoryLicenseTermsAttach]:
    story_data = []
    for log in logs:
        story_data += extract_license_attach(log)

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
                log_index = StoryLicenseTermsAttach.log_index,
                ip_id=StoryLicenseTermsAttach.ip_id,
                license_template=StoryLicenseTermsAttach.license_template,
                license_terms_id=StoryLicenseTermsAttach.license_terms_id,
                block_number=StoryLicenseTermsAttach.block_number,
                transaction_hash=StoryLicenseTermsAttach.transaction_hash
            ) for StoryLicenseTermsAttach in license_attach
        ]
        self._collect_domains(story_license_attached)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[license_attach_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)