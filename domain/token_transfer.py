import logging

from eth_abi import abi
from enumeration.token_type import TokenType
from exporters.jdbc.schema.erc1155_token_transfers import ERC1155TokenTransfers
from exporters.jdbc.schema.erc20_token_transfers import ERC20TokenTransfers
from exporters.jdbc.schema.erc721_token_transfers import ERC721TokenTransfers
from eth_utils import to_normalized_address

TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TRANSFER_SINGLE_EVENT_TOPIC = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
TRANSFER_BATCH_EVENT_TOPIC = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'

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


def format_erc20_token_transfer_data(token_transfer_dict):
    erc20_token_transfer = {
        'model': ERC20TokenTransfers,
        'transaction_hash': token_transfer_dict['transactionHash'],
        'log_index': token_transfer_dict['logIndex'],
        'from_address': to_normalized_address(token_transfer_dict['fromAddress']),
        'to_address': to_normalized_address(token_transfer_dict['toAddress']),
        'value': token_transfer_dict['value'],
        'token_type': token_transfer_dict['tokenType'],
        'token_address': token_transfer_dict['tokenAddress'],

        'block_number': token_transfer_dict['blockNumber'],
        'block_hash': token_transfer_dict['blockHash'],
        'block_timestamp': token_transfer_dict['blockTimestamp']
    }
    return erc20_token_transfer


def format_erc721_token_transfer_data(token_transfer_dict):
    erc721_token_transfer = {
        'model': ERC721TokenTransfers,
        'transaction_hash': token_transfer_dict['transactionHash'],
        'log_index': token_transfer_dict['logIndex'],
        'from_address': to_normalized_address(token_transfer_dict['fromAddress']),
        'to_address': to_normalized_address(token_transfer_dict['toAddress']),
        'token_id': token_transfer_dict['tokenId'],
        'token_type': token_transfer_dict['tokenType'],
        'token_address': token_transfer_dict['tokenAddress'],

        'block_number': token_transfer_dict['blockNumber'],
        'block_hash': token_transfer_dict['blockHash'],
        'block_timestamp': token_transfer_dict['blockTimestamp']
    }
    return erc721_token_transfer


def format_erc1155_token_transfer_data(token_transfer_dict):
    erc1155_token_transfer = {
        'model': ERC1155TokenTransfers,
        'transaction_hash': token_transfer_dict['transactionHash'],
        'log_index': token_transfer_dict['logIndex'],
        'from_address': to_normalized_address(token_transfer_dict['fromAddress']),
        'to_address': to_normalized_address(token_transfer_dict['toAddress']),
        'token_id': token_transfer_dict['tokenId'],
        'value': token_transfer_dict['value'],
        'token_type': token_transfer_dict['tokenType'],
        'token_address': token_transfer_dict['tokenAddress'],

        'block_number': token_transfer_dict['blockNumber'],
        'block_hash': token_transfer_dict['blockHash'],
        'block_timestamp': token_transfer_dict['blockTimestamp']
    }
    return erc1155_token_transfer


def handle_transfer_event(log):
    types = build_types_from_abi(log['topic0'])
    topics_with_data = join_topics_with_data([log['topic1'], log['topic2'], log['topic3']], log['data'])
    from_address, to_address, value = abi.decode(types, bytes.fromhex(topics_with_data))

    # token_type = TokenType.ERC721 if len(log['topics']) > 3 or len(log['topics']) < 2 else TokenType.ERC20

    token_transfer = {
        'transactionHash': log['transaction_hash'],
        'logIndex': log['log_index'],
        'fromAddress': from_address,
        'toAddress': to_address,
        'tokenId': None,
        'value': value,
        'tokenType': None,
        'tokenAddress': log['address'],
        'blockNumber': log['block_number'],
        'blockHash': log['block_hash'],
        'blockTimestamp': log['block_timestamp']
    }

    return token_transfer


def handle_transfer_single_event(log):
    types = build_types_from_abi(log['topic0'])
    topics_with_data = join_topics_with_data([log['topic1'], log['topic2'], log['topic3']], log['data'])
    operator, from_address, to_address, token_id, value = abi.decode(types, bytes.fromhex(topics_with_data))

    token_transfer = {
        'transactionHash': log['transaction_hash'],
        'logIndex': log['log_index'],
        'fromAddress': from_address,
        'toAddress': to_address,
        'tokenId': token_id,
        'value': value,
        'tokenType': TokenType.ERC1155.value,
        'tokenAddress': log['address'],
        'blockNumber': log['block_number'],
        'blockHash': log['block_hash'],
        'blockTimestamp': log['block_timestamp']
    }

    return token_transfer


def handle_transfer_batch_event(log):
    indexed_types, none_indexed_types = build_types_from_abi(log['topic0'])
    topics_with_data = join_topics_with_data([log['topic1'], log['topic2'], log['topic3']])
    data = bytes.fromhex(log['data'][2:])

    op, from_address, to_address = abi.decode(indexed_types, bytes.fromhex(topics_with_data))
    ids, values = abi.decode(none_indexed_types, data)

    if len(ids) != len(values):
        logging.info(f"ids length not equal to values length, log: {log}")
        raise Exception(f"ids length not equal to values length, log: {log}")
    token_transfers = []
    for i, token_id in enumerate(ids):
        token_transfer = {
            'transactionHash': log['transaction_hash'],
            'logIndex': log['log_index'],
            'fromAddress': from_address,
            'toAddress': to_address,
            'tokenId': token_id,
            'value': values[i],
            'tokenType': TokenType.ERC1155.value,
            'tokenAddress': log['address'],
            'blockNumber': log['block_number'],
            'blockHash': log['block_hash'],
            'blockTimestamp': log['block_timestamp']
        }
        token_transfers.append(token_transfer)

    return token_transfers


def extract_transfer_from_log(log):
    token_transfer = None
    topic = log['topic0']

    if topic == TRANSFER_EVENT_TOPIC:
        token_transfer = handle_transfer_event(log)
    elif topic == TRANSFER_SINGLE_EVENT_TOPIC:
        token_transfer = handle_transfer_single_event(log)
    elif topic == TRANSFER_BATCH_EVENT_TOPIC:
        token_transfer = handle_transfer_batch_event(log)

    return token_transfer


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
