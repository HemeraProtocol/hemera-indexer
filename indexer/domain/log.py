from dataclasses import dataclass
from typing import Optional

from eth_utils import to_int, to_normalized_address
from hexbytes import HexBytes

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

    @staticmethod
    def from_rpc(log_dict: dict, block_timestamp=None, block_hash=None, block_number=None):
        topics = log_dict.get("topics", [])
        return Log(
            log_index=to_int(hexstr=log_dict["logIndex"]),
            address=to_normalized_address(log_dict["address"]),
            data=log_dict["data"],
            transaction_hash=log_dict["transactionHash"],
            transaction_index=to_int(hexstr=log_dict["transactionIndex"]),
            block_timestamp=block_timestamp,
            block_number=block_number,
            block_hash=block_hash,
            topic0=topics[0] if len(topics) > 0 else None,
            topic1=topics[1] if len(topics) > 1 else None,
            topic2=topics[2] if len(topics) > 2 else None,
            topic3=topics[3] if len(topics) > 3 else None,
        )

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

    def get_topic_with_data(self) -> HexBytes:
        return self.get_bytes_topics() + self.get_bytes_data()
