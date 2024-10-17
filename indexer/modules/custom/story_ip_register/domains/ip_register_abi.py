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


ip_register_event = Event(
    {
        "anonymous": False,
        "inputs": [
            { "indexed": True, "internalType": "address", "name": "account", "type": "address"},
            { "indexed": True, "internalType": "address", "name": "implementation", "type": "address"},
            { "indexed": True, "internalType": "uint256", "name": "chainId",  "type": "uint256"},
            { "indexed": False, "internalType": "address", "name": "tokenContract", "type": "address"},
            { "indexed": False, "internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "IPAccountRegistered",
        "type": "event",
    }
)

@dataclass
class StoryIpRegistered(Domain):
    transaction_hash: str
    log_index: int
    ip_account: str
    chain_id: int
    token_contract: str
    token_id: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


def handle_ip_register_event(log: Log) -> List[StoryIpRegistered]:
    decode_data = ip_register_event.decode_log_ignore_indexed(log)

    account = decode_data.get("account").lower()
    #imp_address = decode_data.get("implementation").lower()
    chain_id = decode_data.get("chainId")
    token_contract = decode_data.get("tokenContract").lower()
    token_id = decode_data.get("tokenId")

    token_type = "STORY"

    return [
        StoryIpRegistered(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            ip_account=account,
            chain_id=chain_id,
            token_contract=token_contract,
            token_id=token_id,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def extract_ip_register(log: Log) -> List[StoryIpRegistered]:
    story_data = []
    topic = log.topic0

    if topic == ip_register_event.get_signature():
        story_data = handle_ip_register_event(log)

    return story_data

