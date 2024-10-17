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

deposit_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "dst", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Deposit",
        "type": "event",
    }
)

withdraw_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "src", "type": "address"},
            {"indexed": False, "name": "wad", "type": "uint256"},
        ],
        "name": "Withdrawal",
        "type": "event",
    }
)

transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
)

single_transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "id", "type": "uint256"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "TransferSingle",
        "type": "event",
    }
)

batch_transfer_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "ids", "type": "uint256[]"},
            {"indexed": False, "name": "values", "type": "uint256[]"},
        ],
        "name": "TransferBatch",
        "type": "event",
    }
)

@dataclass
class TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: Optional[int]
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int

    def to_specific_transfer(
        self,
    ) -> Union["ERC20TokenTransfer", "ERC721TokenTransfer", "ERC1155TokenTransfer"]:
        common_fields = {
            "transaction_hash": self.transaction_hash,
            "log_index": self.log_index,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "token_address": self.token_address,
            "block_number": self.block_number,
            "block_hash": self.block_hash,
            "block_timestamp": self.block_timestamp,
        }

        if self.token_type == TokenType.ERC20.value:
            return ERC20TokenTransfer(**common_fields, token_type=TokenType.ERC20.value, value=self.value)
        elif self.token_type == TokenType.ERC721.value:
            return ERC721TokenTransfer(**common_fields, token_type=TokenType.ERC721.value, token_id=self.value)
        elif self.token_type == TokenType.ERC1155.value and self.token_id is not None:
            return ERC1155TokenTransfer(
                **common_fields, token_type=TokenType.ERC1155.value, token_id=self.token_id, value=self.value
            )
        elif self.token_type == TokenType.ERC1155.value and self.token_id is None:
            return ERC20TokenTransfer(**common_fields, token_type=TokenType.ERC20.value, value=self.value)
        else:
            raise ValueError(f"Unsupported token type: {self.token_type}")


@dataclass
class ERC20TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int


@dataclass
class ERC721TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int
@dataclass
class ERC1155TokenTransfer(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: int
    value: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int

def handle_deposit_event(log: Log) -> List[TokenTransfer]:
    decode_data = deposit_event.decode_log(log)
    if decode_data is None:
        return []
    wallet_address = decode_data.get("dst").lower()
    value = decode_data.get("wad")
    token_type = TokenType.ERC20.value

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=ZERO_ADDRESS,
            to_address=wallet_address,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_withdraw_event(log: Log) -> List[TokenTransfer]:
    decode_data = withdraw_event.decode_log(log)
    if decode_data is None:
        return []
    wallet_address = decode_data.get("src").lower()
    value = decode_data.get("wad")
    token_type = TokenType.ERC20.value

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=wallet_address,
            to_address=ZERO_ADDRESS,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_event(log: Log) -> List[TokenTransfer]:
    decode_data = transfer_event.decode_log_ignore_indexed(log)

    from_address = decode_data.get("from").lower()
    to_address = decode_data.get("to").lower()
    value = decode_data.get("value")

    token_type = (
        TokenType.ERC721.value
        if log.topic3 or (log.topic1 is None and log.topic2 is None and log.topic3 is None)
        else TokenType.ERC20.value
    )

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=None,
            value=value,
            token_type=token_type,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_single_event(log: Log) -> List[TokenTransfer]:
    decode_data = single_transfer_event.decode_log(log)
    from_address = decode_data.get("from").lower()
    to_address = decode_data.get("to").lower()
    token_id = decode_data.get("id")
    value = decode_data.get("value")

    return [
        TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=token_id,
            value=value,
            token_type=TokenType.ERC1155.value,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
    ]


def handle_transfer_batch_event(log: Log) -> List[TokenTransfer]:
    decode_data = batch_transfer_event.decode_log(log)
    from_address = decode_data["from"].lower()
    to_address = decode_data["to"].lower()
    ids = decode_data["ids"]
    values = decode_data["values"]

    if len(ids) != len(values):
        logging.warning(f"ids length not equal to values length, log: {log}")
        return []

    token_amounts = defaultdict(int)
    for token_id, value in zip(ids, values):
        token_amounts[token_id] += value

    token_transfers = []
    for token_id, total_value in token_amounts.items():
        transfer = TokenTransfer(
            transaction_hash=log.transaction_hash,
            log_index=log.log_index,
            from_address=from_address,
            to_address=to_address,
            token_id=token_id,
            value=total_value,
            token_type=TokenType.ERC1155.value,
            token_address=log.address,
            block_number=log.block_number,
            block_hash=log.block_hash,
            block_timestamp=log.block_timestamp,
        )
        token_transfers.append(transfer)

    return token_transfers

def extract_transfer_from_log(log: Log) -> List[TokenTransfer]:
    token_transfers = []
    topic = log.topic0

    if topic == transfer_event.get_signature():
        token_transfers = handle_transfer_event(log)
    elif topic == deposit_event.get_signature():
        token_transfers = handle_deposit_event(log)
    elif topic == withdraw_event.get_signature():
        token_transfers = handle_withdraw_event(log)
    elif topic == single_transfer_event.get_signature():
        token_transfers = handle_transfer_single_event(log)
    elif topic == batch_transfer_event.get_signature():
        token_transfers = handle_transfer_batch_event(log)
    elif topic == register_event.get_signature():
        token_transfers = handle_register_event(log)

    return token_transfers