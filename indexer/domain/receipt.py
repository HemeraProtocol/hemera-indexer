from dataclasses import field, dataclass
from typing import Optional, List

from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain
from indexer.domain.log import Log


@dataclass
class Receipt(Domain):
    transaction_hash: str
    transaction_index: int
    contract_address: str
    status: int
    logs: List[Log] = field(default_factory=list)
    root: str = Optional[None]
    cumulative_gas_used: Optional[int] = None
    gas_used: Optional[int] = None
    effective_gas_price: Optional[int] = None
    l1_fee: Optional[int] = None
    l1_fee_scalar: Optional[float] = None
    l1_gas_used: Optional[int] = None
    l1_gas_price: Optional[int] = None
    blob_gas_used: Optional[int] = None
    blob_gas_price: Optional[int] = None

    def __init__(self, transaction, receipt_dict: dict):
        self.transaction_hash = receipt_dict['transactionHash']
        self.transaction_index = to_int(hexstr=receipt_dict['transactionIndex'])
        self.contract_address = to_normalized_address(receipt_dict['contractAddress']) \
            if receipt_dict.get('contractAddress', None) else None
        self.status = to_int(hexstr=receipt_dict['status'])
        self.logs = [Log(transaction, log_dict) for log_dict in receipt_dict['logs']]
        self.root = receipt_dict.get('root')
        self.cumulative_gas_used = receipt_dict.get('cumulativeGasUsed')
        self.gas_used = receipt_dict.get('gasUsed')
        self.effective_gas_price = receipt_dict.get('effectiveGasPrice')
        self.l1_fee = receipt_dict.get('l1Fee')
        self.l1_fee_scalar = receipt_dict.get('l1FeeScalar')
        self.l1_gas_used = receipt_dict.get('l1GasUsed')
        self.l1_gas_price = receipt_dict.get('l1GasPrice')
        self.blob_gas_used = receipt_dict.get('blobGasUsed')
        self.blob_gas_price = receipt_dict.get('blobGasPrice')
