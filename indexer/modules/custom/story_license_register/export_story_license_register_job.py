import logging
from typing import List
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.utils.abi import bytes_to_hex_str
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.story_license_register.domains.story_register_license import StoryLicenseRegister,LicensePILRegister
from indexer.modules.custom.story_license_register.license_register_abi import LICENSE_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera.util import calculate_execution_time

logger = logging.getLogger(__name__)

# Constants
TARGET_TOKEN_ADDRESS = ["0x0752f61E59fD2D39193a74610F1bd9a6Ade2E3f9","0x8BB1ADE72E21090Fc891e1d4b88AC5E57b27cB31"]


def handle_license_event(log: Log) -> List[LicensePILRegister]:

    decode_data = LICENSE_EVENT.decode_log(log)
    
    license_terms_id = decode_data.get("licenseTermsId")
    license_template = decode_data.get("licenseTemplate")
    license_terms = decode_data.get("licenseTerms")
    license_str = bytes_to_hex_str(license_terms)
    # if license_str[1282:1346] == None :
    #     byte_sep = ""
    # else:
    #     a = int(license_str[1282:1346],16)
    #     byte_sep = bytes.fromhex(license_str[1346:1346+2*a])
    # print(license_str)
    # print((license_str[1282:1346]))

    return [
        LicensePILRegister(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            license_terms_id= license_terms_id,
            license_template= license_template,

            transferable= bool(license_str[129:130]),
            royalty_policy= "0x" + license_str[154:194],
            default_minting_fee= int(license_str[194:258], 16),
            expiration= int(license_str[258:322], 16),
            commercial_use= bool(int(license_str[322:386])),
            commercial_attribution= bool(int(license_str[386:450])),
            commercializer_checker= "0x" + license_str[474:514],
            commercializer_checker_data= "0x" + license_str[1218:1258],
            commercial_rev_share= int(license_str[578:642], 16),
            commercial_rev_ceiling= int(license_str[642:706], 16),
            derivatives_allowed= bool(int(license_str[706:770])),
            derivatives_attribution= bool(int(license_str[770:834])),
            derivatives_approval= bool(int(license_str[834:898])),
            derivatives_reciprocal= bool(int(license_str[898:962])),
            derivative_rev_ceiling= int(license_str[962:1026],16),
            currency= "0x" + license_str[1050:1090],
            # uri= byte_sep.decode('utf-8'),
            uri="",

            contract_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]

def _filter_license_register(logs: List[Log]) -> List[LicensePILRegister]:
    story_data = []
    for log in logs:
        if log.topic0 == LICENSE_EVENT.get_signature():
            story_data += handle_license_event(log)
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
                contract_address = LicensePILRegister.contract_address,
                block_number=LicensePILRegister.block_number,
                transaction_hash=LicensePILRegister.transaction_hash,
            )
            for LicensePILRegister in license_register
        ]
        self._collect_domains(story_license_register)

    def _process(self, **kwargs):
        pass

    def get_filter(self):
        topic_filter_list = [TopicSpecification(addresses=TARGET_TOKEN_ADDRESS, topics=[LICENSE_EVENT.get_signature()])]

        return TransactionFilterByLogs(topic_filter_list)
