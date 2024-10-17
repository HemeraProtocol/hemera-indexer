import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_token_mint.domains.story_token_mint import StoryLicenseTokenMint
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.modules.custom.story_license_token_mint.domains.token_transfer import (
    StoryLicenseTokenMinted,
    extract_license_token_mint,
    license_token_mint_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0xd81fd78f557b457b4350cB95D20b547bFEb4D857"]


def _filter_mint_tokens(logs: List[Log]) -> List[StoryLicenseTokenMinted]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_license_token_mint(log)
    # return [transfer for transfer in token_transfers if
    #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
    print(token_transfers)
    return token_transfers


class ExportStoryLicenseTokenMintJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryLicenseTokenMint]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            StoryLicenseTokenMint(
                caller=StoryLicenseTokenMinted.caller,
                log_index = StoryLicenseTokenMinted.log_index,
                licensor_ip_id=StoryLicenseTokenMinted.licensor_ip_id,
                license_template=StoryLicenseTokenMinted.license_template,
                license_terms_id=StoryLicenseTokenMinted.license_terms_id,
                amount = StoryLicenseTokenMinted.amount,
                receiver = StoryLicenseTokenMinted.receiver,
                start_license_token_id = StoryLicenseTokenMinted.start_license_token_id,
                block_number=StoryLicenseTokenMinted.block_number,
                transaction_hash=StoryLicenseTokenMinted.transaction_hash
            ) for StoryLicenseTokenMinted in mint_tokens
        ]
        print(erc721_mint_infos)
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[license_token_mint_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)