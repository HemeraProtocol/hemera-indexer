import json
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, cast

from eth_typing import ABIEvent, ABIFunction

from extractor.signature import event_log_abi_to_topic
from extractor.types import Transaction, Base

import logging

@dataclass
class DepositedTransaction(Base):
    msg_hash: str
    version: Optional[int]
    index: Optional[int]
    block_number: int
    block_timestamp: int
    block_hash: str
    transaction_hash: str
    from_address: str
    to_address: str
    local_token_address: Optional[str]
    remote_token_address: Optional[str]
    bridge_from_address: str
    bridge_to_address: str
    amount: int
    extra_info: Dict[str, Any] = field(default_factory=dict)
    bridge_transaction_type: Optional[int] = None

    @property
    def type(self):
        return 'deposited_transaction'


MESSAGE_PASSED_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"gasLimit","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"},{"indexed":false,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"}],"name":"MessagePassed","type":"event"}'))


def parse_message_passed_event(transaction: Transaction, contract_addresses: List[str]) -> List[
    DepositedTransaction]:
    receipt = transaction.receipt
    result = []


    return result