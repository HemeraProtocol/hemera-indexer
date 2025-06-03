from dataclasses import dataclass, field
from typing import List, Optional, Union

from eth_utils import to_int, to_normalized_address

from hemera.indexer.domains import Domain
from hemera.indexer.domains.transaction import Transaction


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
    blob_gas_used: int
    excess_blob_gas: int
    difficulty: int
    size: int
    miner: str
    sha3_uncles: str
    transactions_root: str
    state_root: str
    receipts_root: str
    transactions: Union[List[Transaction], None] = field(default_factory=list)
    total_difficulty: Optional[int] = None
    extra_data: Optional[str] = None
    withdrawals_root: Optional[str] = None

    @staticmethod
    def from_rpc(block_dict: dict):
        transactions = [
            Transaction.from_rpc(
                transaction,
                block_timestamp=to_int(hexstr=block_dict["timestamp"]),
                block_hash=block_dict["hash"],
                block_number=to_int(hexstr=block_dict["number"]),
            )
            for transaction in block_dict.get("transactions", [])
            if transaction
        ]

        return Block(
            number=to_int(hexstr=block_dict["number"]),
            timestamp=to_int(hexstr=block_dict["timestamp"]),
            hash=block_dict["hash"],
            parent_hash=block_dict["parentHash"],
            nonce=block_dict["nonce"],
            gas_limit=to_int(hexstr=block_dict["gasLimit"]),
            gas_used=to_int(hexstr=block_dict["gasUsed"]),
            base_fee_per_gas=to_int(hexstr=block_dict.get("baseFeePerGas", "0")),
            blob_gas_used=to_int(hexstr=block_dict.get("blobGasUsed", "0")),
            excess_blob_gas=to_int(hexstr=block_dict.get("excessBlobGas", "0")),
            difficulty=to_int(hexstr=block_dict["difficulty"]),
            total_difficulty=to_int(hexstr=block_dict.get("totalDifficulty", "0") or "0"),
            size=to_int(hexstr=block_dict["size"]) if "size" in block_dict else 0,
            miner=to_normalized_address(block_dict["miner"]),
            sha3_uncles=block_dict["sha3Uncles"],
            transactions_root=block_dict["transactionsRoot"],
            state_root=block_dict["stateRoot"],
            receipts_root=block_dict["receiptsRoot"],
            transactions=transactions,
            extra_data=block_dict.get("extraData"),
            withdrawals_root=block_dict.get("withdrawalsRoot", None),
        )


@dataclass
class UpdateBlockInternalCount(Domain):
    number: int
    hash: str
    traces_count: Optional[int] = 0
    internal_transactions_count: Optional[int] = 0
