from dataclasses import dataclass, field
from typing import Optional, List

from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain, dict_to_dataclass
from indexer.domain.transaction import Transaction


@dataclass
class Block(Domain):
    number: int
    timestamp: int
    hash: str
    parent_hash: str
    nonce: str
    gas_limit: int
    gas_used: int
    base_fee_per_gas: int
    difficulty: int
    size: int
    miner: str
    sha3_uncles: str
    transactions_root: str
    state_root: str
    receipts_root: str
    transactions: List[Transaction] = field(default_factory=list)
    total_difficulty: Optional[int] = None
    extra_data: Optional[str] = None
    withdrawals_root: Optional[str] = None

    def __init__(self, block_dict: dict, rpc_format=True):
        if rpc_format:
            self.init_from_rpc(block_dict)
        else:
            self.dict_to_entity(block_dict)

    def init_from_rpc(self, block_dict: dict):
        self.number = to_int(hexstr=block_dict['number'])
        self.timestamp = to_int(hexstr=block_dict['timestamp'])
        self.hash = block_dict['hash']
        self.parent_hash = block_dict['parentHash']
        self.nonce = block_dict['nonce']
        self.gas_limit = to_int(hexstr=block_dict['gasLimit'])
        self.gas_used = to_int(hexstr=block_dict['gasUsed'])
        self.base_fee_per_gas = to_int(hexstr=block_dict['baseFeePerGas']) if 'baseFeePerGas' in block_dict else None
        self.difficulty = to_int(hexstr=block_dict['difficulty'])
        self.total_difficulty = to_int(hexstr=block_dict['totalDifficulty'])
        self.size = to_int(hexstr=block_dict['size'])
        self.miner = to_normalized_address(block_dict['miner'])
        self.sha3_uncles = block_dict['sha3Uncles']
        self.transactions_root = block_dict['transactionsRoot']
        self.transactions = [Transaction(block_dict, transaction) for transaction in block_dict['transactions']]
        self.state_root = block_dict['stateRoot']
        self.receipts_root = block_dict['receiptsRoot']
        self.extra_data = block_dict['extraData']
        self.withdrawals_root = block_dict.get('withdrawalsRoot')


def format_block_data(block_dict):
    block = {
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
