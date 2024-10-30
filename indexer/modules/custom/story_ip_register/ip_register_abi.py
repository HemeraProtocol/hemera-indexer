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


IP_REGISTER_EVENT = Event(
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

