import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_attach.domain.story_attach_license import StoryLicenseAttach
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    StoryLicenseTermsAttach,
    extract_license_attach,
    license_attach_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xf49da534215DA7b48E57A41d41dac25C912FCC60"]


def _filter_mint_tokens(logs: List[Log]) -> List[StoryLicenseTermsAttach]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_license_attach(log)
    # return [transfer for transfer in token_transfers if
    #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
    print(token_transfers)
    return token_transfers


class ExportStoryLicenseRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryLicenseAttach]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            StoryLicenseAttach(
                caller=StoryLicenseTermsAttach.caller,
                log_index = StoryLicenseTermsAttach.log_index,
                ip_id=StoryLicenseTermsAttach.ip_id,
                license_template=StoryLicenseTermsAttach.license_template,
                license_terms_id=StoryLicenseTermsAttach.license_terms_id,
                block_number=StoryLicenseTermsAttach.block_number,
                transaction_hash=StoryLicenseTermsAttach.transaction_hash
            ) for StoryLicenseTermsAttach in mint_tokens
        ]
        print(erc721_mint_infos)
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass
        print(self._data_buff[StoryLicenseAttach.type()])

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[license_attach_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)