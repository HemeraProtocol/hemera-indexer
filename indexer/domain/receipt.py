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
    root: Optional[str] = None
    cumulative_gas_used: Optional[int] = None
    gas_used: Optional[int] = None
    effective_gas_price: Optional[int] = None
    l1_fee: Optional[int] = None
    l1_fee_scalar: Optional[float] = None
    l1_gas_used: Optional[int] = None
    l1_gas_price: Optional[int] = None
    blob_gas_used: Optional[int] = None
    blob_gas_price: Optional[int] = None

    @staticmethod
    def from_rpc(receipt_dict: dict, block_timestamp=None, block_hash=None, block_number=None):
        if isinstance(receipt_dict, int):
            print('here')

        logs = [Log.from_rpc(log_dict, block_timestamp, block_hash, block_number) for log_dict in receipt_dict.get('logs', [])]
        return Receipt(
            transaction_hash=receipt_dict['transactionHash'],
            transaction_index=to_int(hexstr=receipt_dict['transactionIndex']),
            contract_address=to_normalized_address(receipt_dict.get('contractAddress')) if receipt_dict.get('contractAddress') else None,
            status=to_int(hexstr=receipt_dict['status']),
            logs=logs,
            root=receipt_dict.get('root'),
            cumulative_gas_used=receipt_dict.get('cumulativeGasUsed'),
            gas_used=receipt_dict.get('gasUsed'),
            effective_gas_price=receipt_dict.get('effectiveGasPrice'),
            l1_fee=receipt_dict.get('l1Fee'),
            l1_fee_scalar=receipt_dict.get('l1FeeScalar'),
            l1_gas_used=receipt_dict.get('l1GasUsed'),
            l1_gas_price=receipt_dict.get('l1GasPrice'),
            blob_gas_used=receipt_dict.get('blobGasUsed'),
            blob_gas_price=receipt_dict.get('blobGasPrice')
        )
