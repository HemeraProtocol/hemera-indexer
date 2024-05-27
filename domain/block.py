from exporters.jdbc.schema.blocks import Blocks
from utils.utils import hex_to_dec, to_normalized_address


def format_block_data(block_dict):
    block = {
        'model': Blocks,
        'number': hex_to_dec(block_dict['number']),
        'timestamp': hex_to_dec(block_dict['timestamp']),
        'hash': block_dict['hash'],
        'parent_hash': block_dict['parentHash'],
        'nonce': block_dict['nonce'],
        'gas_limit': hex_to_dec(block_dict['gasLimit']),
        'gas_used': hex_to_dec(block_dict['gasUsed']),
        'base_fee_per_gas': hex_to_dec(block_dict['baseFeePerGas']),
        'difficulty': hex_to_dec(block_dict['difficulty']),
        'total_difficulty': hex_to_dec(block_dict['totalDifficulty']),
        'size': hex_to_dec(block_dict['size']),
        'miner': to_normalized_address(block_dict['miner']),
        'sha3_uncles': block_dict['sha3Uncles'],
        'transactions_root': block_dict['transactionsRoot'],
        'transactions_count': len(block_dict['transactions']),
        'state_root': block_dict['stateRoot'],
        'receipts_root': block_dict['receiptsRoot'],
        'extra_data': block_dict['extraData'],
        'withdrawals_root': block_dict.get('withdrawalsRoot')
    }

    return block
