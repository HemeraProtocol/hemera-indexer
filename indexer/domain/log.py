from dataclasses import dataclass
from typing import Optional

from hexbytes import HexBytes

from common.models.logs import Logs
from eth_utils import to_int, to_normalized_address

from indexer.domain import Domain


@dataclass
class Log(Domain):
    log_index: int
    address: str
    data: str
    transaction_hash: str
    transaction_index: int
    block_timestamp: int
    block_number: int
    block_hash: str
    topic0: Optional[str] = None
    topic1: Optional[str] = None
    topic2: Optional[str] = None
    topic3: Optional[str] = None

    def __init__(self, transaction, log_dict: dict):
        self.log_index = to_int(hexstr=log_dict['logIndex'])
        self.address = to_normalized_address(log_dict['address'])
        self.data = log_dict['data']
        self.topic0 = log_dict['topics'][0] if len(log_dict['topics']) > 0 else None
        self.topic1 = log_dict['topics'][1] if len(log_dict['topics']) > 1 else None
        self.topic2 = log_dict['topics'][2] if len(log_dict['topics']) > 2 else None
        self.topic3 = log_dict['topics'][3] if len(log_dict['topics']) > 3 else None
        self.transaction_hash = log_dict['transactionHash']
        self.transaction_index = to_int(hexstr=log_dict['transactionIndex'])
        self.block_number = transaction.block_number
        self.block_hash = transaction.block_hash
        self.block_timestamp = transaction.block_timestamp

    def get_bytes_topics(self) -> HexBytes:
        topics = ""
        for i in range(4):
            topic = getattr(self, f"topic{i}")
            if topic and i != 0:
                if topic.startswith("0x"):
                    topic = topic[2:]
                topics += topic
        return HexBytes(bytearray.fromhex(topics))

    def get_bytes_data(self) -> HexBytes:
        data = self.data
        if data.startswith("0x"):
            data = self.data[2:]
        return HexBytes(bytearray.fromhex(data))
