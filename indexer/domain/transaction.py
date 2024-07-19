from dataclasses import dataclass, field
from typing import Optional, List

from common.models.transactions import Transactions
from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain
from indexer.domain.receipt import Receipt


@dataclass
class Transaction(Domain):
    hash: str
    nonce: int
    transaction_index: int
    from_address: str
    to_address: Optional[str]
    value: int
    gas_price: int
    gas: int
    transaction_type: int
    input: str
    block_number: int
    block_timestamp: int
    block_hash: str
    blob_versioned_hashes: List[str] = field(default_factory=list)
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    receipt: Receipt = None

    # may occur KeyError, should check and fix later
    exist_error: Optional[bool] = False
    error: Optional[str] = None
    revert_reason: Optional[str] = None

    def __init__(self, block_dict=None, transaction_dict=None, rpc_format=True):
        if rpc_format:
            self.init_from_rpc(block_dict, transaction_dict)
        else:
            self.dict_to_entity(transaction_dict)

    def init_from_rpc(self, block_dict: dict, transaction_dict: dict):
        self.hash = transaction_dict['hash']
        self.transaction_index = to_int(hexstr=transaction_dict['transactionIndex'])
        self.from_address = to_normalized_address(transaction_dict['from']) if transaction_dict['to'] else None
        self.to_address = to_normalized_address(transaction_dict['to']) if transaction_dict['to'] else None
        self.value = to_int(hexstr=transaction_dict['value'])
        self.transaction_type = to_int(hexstr=transaction_dict['type']) if transaction_dict['type'] else None
        self.input = transaction_dict['input']
        self.nonce = to_int(hexstr=transaction_dict['nonce'])
        self.block_hash = block_dict['hash']
        self.block_number = to_int(hexstr=block_dict['number'])
        self.block_timestamp = to_int(hexstr=block_dict['timestamp'])
        self.gas = to_int(hexstr=transaction_dict['gas'])
        self.gas_price = to_int(hexstr=transaction_dict['gasPrice'])
        self.max_fee_per_gas = to_int(hexstr=transaction_dict.get('maxFeePerGas')) \
            if transaction_dict.get('maxFeePerGas', None) else None
        self.max_priority_fee_per_gas = to_int(hexstr=transaction_dict.get('maxPriorityFeePerGas')) \
            if transaction_dict.get('maxPriorityFeePerGas', None) else None
        self.blob_versioned_hashes = transaction_dict.get('blobVersionedHashes', [])
        self.error = transaction_dict.get('error', None)
        self.exist_error = self.error is not None
        self.revert_reason = transaction_dict.get('revertReason', None)

    def fill_with_receipt(self, receipt: Receipt):
        self.receipt = receipt
