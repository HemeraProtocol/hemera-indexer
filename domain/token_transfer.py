import logging
from eth_abi import abi
from enumeration.token_type import TokenType
from utils.utils import hex_to_dec, to_normalized_address, chunk_string
from exporters.jdbc.schema.token_transfers import TokenTransfers

TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TRANSFER_SINGLE_EVENT_TOPIC = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
TRANSFER_BATCH_EVENT_TOPIC = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'

logger = logging.getLogger(__name__)


def format_token_transfer_data(token_transfer_dict):
    token_transfer = {
        'model': TokenTransfers,
        'transaction_hash': token_transfer_dict['transactionHash'],
        'log_index': hex_to_dec(token_transfer_dict['logIndex']),
        'from_address': to_normalized_address(token_transfer_dict['fromAddress']),
        'to_address': to_normalized_address(token_transfer_dict['toAddress']),
        'amount': hex_to_dec(token_transfer_dict['amount']),
        'token_id': token_transfer_dict['tokenId'],
        'token_type': token_transfer_dict['tokenType'],
        'token_address': token_transfer_dict['tokenAddress'],

        'block_number': hex_to_dec(token_transfer_dict['blockNumber']),
        'block_hash': token_transfer_dict['blockHash'],
        'block_timestamp': hex_to_dec(token_transfer_dict['blockTimestamp'])
    }
    return token_transfer


def handle_transfer_event(log):
    topics = [topic for topic in log['topics']]

    token_type = TokenType.ERC721 if len(topics) > 3 or len(topics) < 2 else TokenType.ERC20

    topics_with_data = "".join(list(map(lambda x: x[2:], topics))) + log['data'][2:]

    token_transfer = {
        'transactionHash': log['transactionHash'],
        'logIndex': log['logIndex'],
        'fromAddress': "0x" + topics_with_data[88:128],
        'toAddress': "0x" + topics_with_data[152:192],
        'amount': "0x" + topics_with_data[192:256],
        'tokenId': None,
        'tokenType': token_type.value,
        'tokenAddress': log['address'],
        'blockNumber': log['blockNumber'],
        'blockHash': log['blockHash'],
    }

    return token_transfer


def handle_transfer_single_event(log):
    topics = [topic for topic in log['topics']]

    topics_with_data = topics + split_to_words(log['data'])

    token_transfer = {
        'transactionHash': log['transactionHash'],
        'logIndex': log['logIndex'],
        'fromAddress': word_to_address(topics_with_data[2]),
        'toAddress': word_to_address(topics_with_data[3]),
        'amount': topics_with_data[5],
        'tokenId': topics_with_data[4],
        'tokenType': TokenType.ERC1155.value,
        'tokenAddress': log['address'],
        'blockNumber': log['blockNumber'],
        'blockHash': log['blockHash'],
    }

    return token_transfer


def handle_transfer_batch_event(log):
    topics_with_data = "".join([topic[2:] for topic in log['topics'][1:]])
    data = bytes.fromhex(log['data'][2:])

    op, from_address, to_address = abi.decode(['address', 'address', 'address'], topics_with_data)
    ids, values = abi.decode(['uint256[]', 'uint256[]'], data)

    if len(ids) != len(values):
        logging.info(f"ids length not equal to values length, log: {log}")
        raise Exception(f"ids length not equal to values length, log: {log}")
    token_transfers = []
    for i, token_id in enumerate(ids):
        token_transfer = {
            'transactionHash': log['transactionHash'],
            'logIndex': log['logIndex'],
            'fromAddress': from_address,
            'toAddress': to_address,
            'amount': values[i],
            'tokenId': token_id,
            'tokenType': TokenType.ERC1155.value,
            'tokenAddress': log['address'],
            'blockNumber': log['blockNumber'],
            'blockHash': log['blockHash'],
        }
        token_transfers.append(token_transfer)

    return token_transfers


def extract_transfer_from_log(log):
    token_transfer = None
    topic = log['topics'][0]

    if topic == TRANSFER_EVENT_TOPIC:
        token_transfer = handle_transfer_event(log)
    elif topic == TRANSFER_SINGLE_EVENT_TOPIC:
        token_transfer = handle_transfer_single_event(log)
    elif topic == TRANSFER_BATCH_EVENT_TOPIC:
        token_transfer = handle_transfer_batch_event(log)

    return token_transfer


def split_to_words(data):
    if data and len(data) > 2:
        data_without_0x = data[2:]
        words = list(chunk_string(data_without_0x, 64))
        words_with_0x = list(map(lambda word: '0x' + word, words))
        return words_with_0x
    return []


def word_to_address(param):
    if param is None:
        return None
    elif len(param) >= 40:
        return to_normalized_address('0x' + param[-40:])
    else:
        return to_normalized_address(param)
