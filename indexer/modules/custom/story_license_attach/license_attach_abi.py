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

license_attach_event = Event(
    
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "caller",
				"type": "address"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "ipId",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "address",
				"name": "licenseTemplate",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "licenseTermsId",
				"type": "uint256"
			}
		],
		"name": "LicenseTermsAttached",
		"type": "event",
	},
)  


@dataclass
class StoryLicenseTermsAttach(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    ip_id: str
    license_template: str
    license_terms_id: int
    contract_address: str
    block_number: int
    block_timestamp: int


def handle_license_attach_event(log: Log) -> List[StoryLicenseTermsAttach]:
    decode_data = license_attach_event.decode_log_ignore_indexed(log)

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


def extract_license_attach(log: Log) -> List[StoryLicenseTermsAttach]:
    story_data = []
    topic = log.topic0

    if topic == license_attach_event.get_signature():
        story_data = handle_license_attach_event(log)

    return story_data