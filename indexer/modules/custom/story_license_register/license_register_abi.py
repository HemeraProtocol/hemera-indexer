import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Union, Sequence,Tuple,Any
from indexer.utils.abi import bytes_to_hex_str
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.utils.abi import Event
from indexer.utils.utils import ZERO_ADDRESS

logger = logging.getLogger(__name__)


license_event = Event(
    {
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "uint256",
				"name": "licenseTermsId",
				"type": "uint256"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "licenseTemplate",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "bytes",
				"name": "licenseTerms",
				"type": "bytes"
			}
		],
		"name": "LicenseTermsRegistered",
		"type": "event",
	}
)

@dataclass
class LicensePILRegister(Domain):
    transaction_hash: str
    log_index: int
    license_terms_id: int
    license_template: str
    transferable: bool
    royalty_policy: str
    default_minting_fee: int
    expiration: int
    commercial_use: bool
    commercial_attribution: bool
    commercializer_checker: str
    commercializer_checker_data: bytes
    commercial_rev_share: int
    commercial_rev_ceiling: int
    derivatives_allowed: bool
    derivatives_attribution: bool
    derivatives_approval: bool
    derivatives_reciprocal: bool
    derivative_rev_ceiling: int
    currency: str
    uri: str
    contract_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


def handle_license_event(log: Log) -> List[LicensePILRegister]:

    decode_data = license_event.decode_log(log)
    
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

def extract_license_register(log: Log) -> List[LicensePILRegister]:
    story_data = []
    topic = log.topic0

    if topic == license_event.get_signature():
        story_data = handle_license_event(log)

    return story_data