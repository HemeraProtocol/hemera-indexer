import logging
from typing import Dict, List

from eth_utils import to_checksum_address

from models.bridge.bedrock.parser.bedrock_bridge_parser import parse_relayed_message, \
    parse_message_passed_event, BEDROCK_EVENT_ABI_SIGNATURE_MAPPING
from models.bridge.extractor import Extractor
from models.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L2, L2_TO_L1_WITHDRAWN_TRANSACTION_ON_l2
from models.types import dict_to_dataclass, Transaction

logger = logging.getLogger(__name__)


class L2BridgeDataExtractor(Extractor):

    def __init__(self, l2_to_l1_message_passer=None, l2_cross_domain_messenger=None):
        super().__init__()
        self.l2_to_l1_message_passer = l2_to_l1_message_passer
        self.l2_cross_domain_messenger = l2_cross_domain_messenger

        assert self.l2_to_l1_message_passer and self.l2_cross_domain_messenger, "Both l2_to_l1_message_passer and l2_cross_domain_messenger must be provided."

    def get_filter(self):
        topics = [
            BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["RELAYED_MESSAGE_EVENT"],
            BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["MESSAGE_PASSED_EVENT"],
        ]
        addresses = [self.l2_to_l1_message_passer, self.l2_cross_domain_messenger]

        filter_params = {
            "topics": [
                topics
            ],
            "address": [
                to_checksum_address(address) for address in addresses
            ],
        }
        return filter_params

    def extract_bridge_data(self, transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        transactions = [(dict_to_dataclass(tx, Transaction)) for tx in transactions]

        relay_transactions = [
            {
                "item": L1_TO_L2_DEPOSITED_TRANSACTION_ON_L2,
                "msg_hash": relay_transaction.msg_hash,
                "l2_block_number": relay_transaction.block_number,
                "l2_block_timestamp": relay_transaction.block_timestamp,
                "l2_block_hash": relay_transaction.block_hash,
                "l2_transaction_hash": relay_transaction.transaction_hash,
                "l2_from_address": relay_transaction.from_address,
                "l2_to_address": relay_transaction.to_address,
            }
            for transaction in transactions
            for relay_transaction in parse_relayed_message(
                "RELAYED_MESSAGE_EVENT",
                transaction,
                self.l2_cross_domain_messenger,
                "msgHash"
            )
        ]

        l2_to_l1_withdrawal_transactions = [
            {
                "item": L2_TO_L1_WITHDRAWN_TRANSACTION_ON_l2,
                "msg_hash": withdrawn_transaction.withdrawal_hash,
                "version": withdrawn_transaction.version,
                "index": withdrawn_transaction.index,
                "l2_block_number": withdrawn_transaction.block_number,
                "l2_block_timestamp": withdrawn_transaction.block_timestamp,
                "l2_block_hash": withdrawn_transaction.block_hash,
                "l2_transaction_hash": withdrawn_transaction.transaction_hash,
                "l2_from_address": withdrawn_transaction.from_address,
                "l2_to_address": withdrawn_transaction.to_address,
                "amount": withdrawn_transaction.amount,
                "from_address": withdrawn_transaction.bridge_from_address,
                "to_address": withdrawn_transaction.bridge_to_address,
                "l1_token_address": withdrawn_transaction.local_token_address,
                "l2_token_address": withdrawn_transaction.remote_token_address,
                "extra_info": withdrawn_transaction.extra_info,
                "_type": withdrawn_transaction.bridge_transaction_type,
                "target": withdrawn_transaction.target,
                "sender": withdrawn_transaction.sender,
                "data": withdrawn_transaction.message,
            }
            for transaction in transactions
            for withdrawn_transaction in parse_message_passed_event(
                transaction,
                self.l2_to_l1_message_passer
            )
        ]

        return relay_transactions + l2_to_l1_withdrawal_transactions
