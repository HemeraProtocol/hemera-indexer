from exporters.jdbc.schema.blocks import Blocks
from eth_utils import to_int, to_normalized_address


def format_block_data(block_dict):
    block = {
        'model': Blocks,
        'number': to_int(hexstr=block_dict['number']),
        'timestamp': to_int(hexstr=block_dict['timestamp']),
        'hash': block_dict['hash'],
        'parent_hash': block_dict['parentHash'],
        'nonce': block_dict['nonce'],
        'gas_limit': to_int(hexstr=block_dict['gasLimit']),
        'gas_used': to_int(hexstr=block_dict['gasUsed']),
        'base_fee_per_gas': to_int(hexstr=block_dict['baseFeePerGas']) if 'baseFeePerGas' in block_dict else None,
        'difficulty': to_int(hexstr=block_dict['difficulty']),
        'total_difficulty': to_int(hexstr=block_dict['totalDifficulty']),
        'size': to_int(hexstr=block_dict['size']),
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
