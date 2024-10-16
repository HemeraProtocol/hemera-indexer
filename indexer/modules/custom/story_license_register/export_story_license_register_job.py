import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_register.domain.story_register_license import StoryLicenseRegister
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.domain.token_transfer import (
    LicensePILRegister,
    extract_license_register,
    license_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x8BB1ADE72E21090Fc891e1d4b88AC5E57b27cB31"]


def _filter_mint_tokens(logs: List[Log]) -> List[LicensePILRegister]:
    token_transfers = []
    for log in logs:
        token_transfers += extract_license_register(log)
    # return [transfer for transfer in token_transfers if
    #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
    print(token_transfers)
    return token_transfers


class ExportStoryLicenseRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryLicenseRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        mint_tokens = _filter_mint_tokens(logs)

        erc721_mint_infos = [
            StoryLicenseRegister(
                license_terms_id=LicensePILRegister.license_terms_id,
                license_template=LicensePILRegister.license_template,
                transferable=LicensePILRegister.transferable,
                royalty_policy=LicensePILRegister.royalty_policy,
                default_minting_fee=LicensePILRegister.default_minting_fee,
                expiration=LicensePILRegister.expiration,
                commercial_use=LicensePILRegister.commercial_use,
                commercial_attribution=LicensePILRegister.commercial_attribution,
                commercializer_checker=LicensePILRegister.commercializer_checker,
                commercializer_checker_data=LicensePILRegister.commercializer_checker_data,
                commercial_rev_share=LicensePILRegister.commercial_rev_share,
                commercial_rev_ceiling=LicensePILRegister.commercial_rev_ceiling,
                derivatives_allowed=LicensePILRegister.derivatives_allowed,
                derivatives_attribution=LicensePILRegister.derivatives_attribution,
                derivatives_approval=LicensePILRegister.derivatives_approval,
                derivatives_reciprocal=LicensePILRegister.derivatives_reciprocal,
                derivative_rev_ceiling=LicensePILRegister.derivative_rev_ceiling,
                currency=LicensePILRegister.currency,
                uri=LicensePILRegister.uri,
                block_number=LicensePILRegister.block_number,
                transaction_hash=LicensePILRegister.transaction_hash
            ) for LicensePILRegister in mint_tokens
        ]
        print(erc721_mint_infos)
        self._collect_domains(erc721_mint_infos)

    def _process(self, **kwargs):
        pass
        print(self._data_buff[StoryLicenseRegister.type()])

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[license_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)