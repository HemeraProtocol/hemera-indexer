import logging
from dataclasses import dataclass
from typing import List, Union

from eth_abi import abi
from enumeration.token_type import TokenType
from eth_utils import to_normalized_address

from indexer.domain import Domain
from indexer.domain.log import Log
from indexer.utils.utils import (
    DEPOSIT_EVENT_TOPIC,
    WITHDRAW_EVENT_TOPIC,
    TRANSFER_EVENT_TOPIC,
    TRANSFER_SINGLE_EVENT_TOPIC,
    TRANSFER_BATCH_EVENT_TOPIC
)

logger = logging.getLogger(__name__)

transfer_abi = {
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62": {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "id", "type": "uint256"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "TransferSingle",
        "type": "event"
    },
    "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb": {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "operator", "type": "address"},
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "ids", "type": "uint256[]"},
            {"indexed": False, "name": "values", "type": "uint256[]"}
        ],
        "name": "TransferSingle",
        "type": "event"
    }
}


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


def handle_transfer_event(log: Log) -> Union[ERC20TokenTransfer, ERC721TokenTransfer]:
    types = build_types_from_abi(log.topic0)
    topics_with_data = join_topics_with_data([log.topic1, log.topic2, log.topic3], log.data)
    from_address, to_address, value = abi.decode(types, bytes.fromhex(topics_with_data))

    token_type = TokenType.ERC721.value \
        if log.topic3 or (log.topic1 is None and log.topic2 is None and log.topic3 is None) \
        else TokenType.ERC20.value

    if log.topic0 == DEPOSIT_EVENT_TOPIC or log.topic0 == WITHDRAW_EVENT_TOPIC:
        token_type = TokenType.ERC20.value

    transfer_dict = {
        'transaction_hash': log.transaction_hash,
        'log_index': log.log_index,
        'from_address': to_normalized_address(from_address),
        'to_address': to_normalized_address(to_address),
        'token_type': token_type,
        'token_address': log.address,
        'block_number': log.block_number,
        'block_hash': log.block_hash,
        'block_timestamp': log.block_timestamp
    }

    if token_type == TokenType.ERC20.value:
        transfer_dict['value'] = value
        token_transfer = ERC20TokenTransfer(**transfer_dict)
    else:
        transfer_dict['token_id'] = value
        token_transfer = ERC721TokenTransfer(**transfer_dict)

    return token_transfer


def handle_transfer_single_event(log: Log) -> ERC1155TokenTransfer:
    types = build_types_from_abi(log.topic0)
    topics_with_data = join_topics_with_data([log.topic1, log.topic2, log.topic3], log.data)
    operator, from_address, to_address, token_id, value = abi.decode(types, bytes.fromhex(topics_with_data))

    transfer_dict = {
        'transaction_hash': log.transaction_hash,
        'log_index': log.log_index,
        'from_address': to_normalized_address(from_address),
        'to_address': to_normalized_address(to_address),
        'token_id': token_id,
        'value': value,
        'token_type': TokenType.ERC1155.value,
        'token_address': log.address,
        'block_number': log.block_number,
        'block_hash': log.block_hash,
        'block_timestamp': log.block_timestamp
    }

    return ERC1155TokenTransfer(**transfer_dict)


def handle_transfer_batch_event(log: Log) -> List[ERC1155TokenTransfer]:
    indexed_types, none_indexed_types = build_types_from_abi(log.topic0)
    topics_with_data = join_topics_with_data([log.topic1, log.topic2, log.topic3])
    data = bytes.fromhex(log.data[2:])

    op, from_address, to_address = abi.decode(indexed_types, bytes.fromhex(topics_with_data))
    ids, values = abi.decode(none_indexed_types, data)

    if len(ids) != len(values):
        logging.info(f"ids length not equal to values length, log: {log}")
        raise Exception(f"ids length not equal to values length, log: {log}")

    token_id_transfers = {}
    for i, token_id in enumerate(ids):
        transfer_dict = {
            'transaction_hash': log.transaction_hash,
            'log_index': log.log_index,
            'from_address': to_normalized_address(from_address),
            'to_address': to_normalized_address(to_address),
            'token_id': token_id,
            'value': values[i],
            'token_type': TokenType.ERC1155.value,
            'token_address': log.address,
            'block_number': log.block_number,
            'block_hash': log.block_hash,
            'block_timestamp': log.block_timestamp
        }
        if token_id not in token_id_transfers:
            token_id_transfers[token_id] = ERC1155TokenTransfer(**transfer_dict)
        else:
            token_id_transfers[token_id].value += values[i]

    token_transfers = []
    for token_id in token_id_transfers.keys():
        token_transfers.append(token_id_transfers[token_id])

    return token_transfers


def extract_transfer_from_log(log: Log) \
        -> List[Union[ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer]]:
    token_transfers = []
    topic = log.topic0

    if topic == TRANSFER_EVENT_TOPIC:
        token_transfers = [handle_transfer_event(log)]
    elif topic == TRANSFER_SINGLE_EVENT_TOPIC:
        token_transfers = [handle_transfer_single_event(log)]
    elif topic == TRANSFER_BATCH_EVENT_TOPIC:
        token_transfers = handle_transfer_batch_event(log)

    return token_transfers


def build_types_from_abi(topic0):
    abi_info = transfer_abi[topic0]

    if topic0 == TRANSFER_BATCH_EVENT_TOPIC:
        indexed_types, none_indexed_types = [], []
        for data_input in abi_info['inputs']:
            if data_input['indexed']:
                indexed_types.append(data_input['type'])
            else:
                none_indexed_types.append(data_input['type'])

        return indexed_types, none_indexed_types
    else:
        types = [data_input['type'] for data_input in abi_info['inputs']]
        return types


def join_topics_with_data(topics, data=None):
    topics_with_data = "".join([topic[2:] for topic in topics if topic is not None])

    if data is not None:
        topics_with_data += data[2:]

    return topics_with_data
