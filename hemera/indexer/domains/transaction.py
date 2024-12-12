from dataclasses import dataclass, field
from typing import List, Optional

from eth_utils import to_int, to_normalized_address

from hemera.indexer.domains import Domain
from hemera.indexer.domains.receipt import Receipt


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
    transaction_type: Optional[int]
    input: str
    block_number: int
    block_timestamp: int
    block_hash: str
    blob_versioned_hashes: List[str] = field(default_factory=list)
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    receipt: Optional[Receipt] = None
    exist_error: Optional[bool] = False
    error: Optional[str] = None
    revert_reason: Optional[str] = None

    @staticmethod
    def from_rpc(transaction_dict: dict, block_timestamp=None, block_hash=None, block_number=None):
        return Transaction(
            hash=transaction_dict["hash"],
            transaction_index=to_int(hexstr=transaction_dict["transactionIndex"]),
            from_address=to_normalized_address(transaction_dict["from"]),
            to_address=(to_normalized_address(transaction_dict["to"]) if transaction_dict.get("to") else None),
            value=to_int(hexstr=transaction_dict["value"]),
            transaction_type=to_int(hexstr=transaction_dict.get("type", "0")),
            input=transaction_dict["input"],
            nonce=to_int(hexstr=transaction_dict["nonce"]),
            block_hash=block_hash,
            block_number=block_number,
            block_timestamp=block_timestamp,
            gas=to_int(hexstr=transaction_dict["gas"]),
            gas_price=to_int(hexstr=transaction_dict["gasPrice"]) if "gasPrice" in transaction_dict else None,
            max_fee_per_gas=(
                to_int(hexstr=transaction_dict.get("maxFeePerGas"))
                if transaction_dict.get("maxFeePerGas", None)
                else None
            ),
            max_priority_fee_per_gas=(
                to_int(hexstr=transaction_dict.get("maxPriorityFeePerGas"))
                if transaction_dict.get("maxPriorityFeePerGas", None)
                else None
            ),
            blob_versioned_hashes=transaction_dict.get("blobVersionedHashes", []),
            error=transaction_dict.get("error"),
            exist_error=transaction_dict.get("error") is not None,
            revert_reason=transaction_dict.get("revertReason"),
        )

    def fill_with_receipt(self, receipt: Receipt):
        self.receipt = receipt
        if self.to_address is None:
            self.to_address = self.receipt.contract_address

    def get_method_id(self):
        return self.input[0:10] if self.input and len(self.input) > 10 else None
