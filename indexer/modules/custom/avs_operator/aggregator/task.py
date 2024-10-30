from dataclasses import dataclass
from typing import List

from eth_abi import encode
from eth_hash.auto import keccak


@dataclass
class AlertTaskInfo:
    alert_hash: bytes
    quorum_numbers: List[int]
    quorum_threshold_percentages: List[int]
    task_index: int
    reference_block_number: int

    def encode_sig_hash(self):
        types = ['bytes32', 'uint32']

        # Pack the data
        values = [
            self.alert_hash,
            self.reference_block_number
        ]
        encoded = encode(types, values)
        return encoded

    def sign_hash(self):
        alert_bytes = self.encode_sig_hash()

        hasher = keccak.new(alert_bytes)

        # Get the hash and return it as a 32-byte array
        hash_bytes = hasher.digest()
        return hash_bytes[:32]
