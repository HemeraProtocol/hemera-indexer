import logging
from typing import List

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_register.domains.story_register_license import StoryLicenseRegister
from indexer.utils.multicall_hemera.util import calculate_execution_time
from indexer.utils.utils import ZERO_ADDRESS
from indexer.modules.custom.story_license_register.domains.license_register_abi import (
    LicensePILRegister,
    extract_license_register,
    license_event,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x0752f61E59fD2D39193a74610F1bd9a6Ade2E3f9"]


def _filter_license_register(logs: List[Log]) -> List[LicensePILRegister]:
    story_data = []
    for log in logs:
        story_data += extract_license_register(log)
    return story_data


class ExportStoryLicenseRegisterJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [StoryLicenseRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @calculate_execution_time
    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        license_register = _filter_license_register(logs)

        story_license_register = [
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
            ) for LicensePILRegister in license_register
        ]
        self._collect_domains(story_license_register)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=TARGET_TOKEN_ADDRESS, topics=[license_event.get_signature()]
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)