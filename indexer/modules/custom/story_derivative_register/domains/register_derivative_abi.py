import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Union, Sequence,Tuple,Any
from indexer.utils.abi import bytes_to_hex_str
from enumeration.token_type import TokenType
from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.utils.abi import Event
from indexer.utils.utils import ZERO_ADDRESS

logger = logging.getLogger(__name__)

derivative_registered_event = Event(
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
				"name": "childIpId",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256[]",
				"name": "licenseTokenIds",
				"type": "uint256[]"
			},
			{
				"indexed": False,
				"internalType": "address[]",
				"name": "parentIpIds",
				"type": "address[]"
			},
			{
				"indexed": False,
				"internalType": "uint256[]",
				"name": "licenseTermsIds",
				"type": "uint256[]"
			},
			{
				"indexed": False,
				"internalType": "address",
				"name": "licenseTemplate",
				"type": "address"
			}
		],
		"name": "DerivativeRegistered",
		"type": "event"
	},

)

@dataclass
class StoryDerivativeRegistered(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    child_ip_id: str
    license_token_ids: List[int]
    parent_ip_ids: List[str]
    license_terms_ids : List[int]
    license_template: str
    block_number: int
    block_timestamp: int

def handle_derivative_registered_event(log: Log) -> List[StoryDerivativeRegistered]:
    decode_data = derivative_registered_event.decode_log(log)

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
            block_number=log.block_number,
            block_timestamp=log.block_timestamp,
        )
    ]

def extract_derivative_registered(log: Log) -> List[StoryDerivativeRegistered]:
    story_data = []
    topic = log.topic0

    if topic == derivative_registered_event.get_signature():
        story_data = handle_derivative_registered_event(log)

    return story_data