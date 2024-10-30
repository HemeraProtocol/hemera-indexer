from dataclasses import dataclass
from hashlib import sha3_256

from indexer.domain import FilterData
from indexer.domain.log import Log


@dataclass
class HemeraHistoryTransparency(FilterData):
    start_block: int
    end_block: int
    data_class: bytes
    code_hash: bytes
    data_hash: bytes
    msg_hash: bytes
    count: int
    verify_status: bool
    confirm_status: bool

    def message_hash(self):
        hasher = sha3_256()
        hasher.update(self.data_class)
        hasher.update(self.code_hash)
        hasher.update(self.data_hash)
        hasher.update(self.start_block.to_bytes(32, 'big'))
        hasher.update(self.end_block.to_bytes(32, 'big'))
        hasher.update(self.count.to_bytes(32, 'big'))
        return hasher.digest()[:32]


@dataclass
class LogWithDecodeData:
    log: Log
    decode_data: dict
    verified: bool = False