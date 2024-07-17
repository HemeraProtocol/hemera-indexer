import logging
from typing import Dict, List

from eth_utils import to_checksum_address

from models.bridge.bedrock.parser.bedrock_bridge_parser import parse_transaction_deposited_event, \
    parse_relayed_message, \
    parse_propose_l2_output, BEDROCK_EVENT_ABI_SIGNATURE_MAPPING
from models.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN, \
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED


from models.bridge.bedrock.extractor.extractor import Extractor
from models.bridge.types import dict_to_dataclass, Transaction

logger = logging.getLogger(__name__)


class L1BridgeDataExtractor(Extractor):

    def __init__(self, optimism_portal_proxy=None, l2_output_oracle_proxy=None):
        super().__init__()
        self.optimism_portal_proxy = optimism_portal_proxy
        self.l2_output_oracle_proxy = l2_output_oracle_proxy

        if self.optimism_portal_proxy:
            logger.info(f"OptimismPortalProxy: {self.optimism_portal_proxy}")
            self.optimism_portal_proxy = self.optimism_portal_proxy.lower()
        else:
            logger.warning("OptimismPortalProxy is None")
        if self.l2_output_oracle_proxy:
            logger.info(f"L2OutputOracleProxy: {self.l2_output_oracle_proxy}")
            self.l2_output_oracle_proxy = self.l2_output_oracle_proxy.lower()
        else:
            logger.warning("L2OutputOracleProxy is None")

    def get_filter(self):
        topics = []
        addresses = []

        if self.optimism_portal_proxy:
            addresses.append(self.optimism_portal_proxy)
            topics.append(BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["WITHDRAWAL_FINALIZED_EVENT"])
            topics.append(BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["WITHDRAWAL_PROVEN_EVENT"])
            topics.append(BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["TRANSACTION_DEPOSITED_EVENT"])
        if self.l2_output_oracle_proxy:
            addresses.append(self.l2_output_oracle_proxy)
            topics.append(BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["OUTPUT_PROPOSED_EVENT"])
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

        result = []
        transactions = [(dict_to_dataclass(tx, Transaction)) for tx in transactions]

        if self.optimism_portal_proxy:
            l1_to_l2_deposit_transactions = [
                {
                    "item": L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1,
                    "msg_hash": deposited_transaction.msg_hash,
                    "version": deposited_transaction.version,
                    "index": deposited_transaction.index,
                    "l1_block_number": deposited_transaction.block_number,
                    "l1_block_timestamp": deposited_transaction.block_timestamp,
                    "l1_block_hash": deposited_transaction.block_hash,
                    "l1_transaction_hash": deposited_transaction.transaction_hash,
                    "l1_from_address": deposited_transaction.from_address,
                    "l1_to_address": deposited_transaction.to_address,
                    "amount": deposited_transaction.amount,
                    "from_address": deposited_transaction.bridge_from_address,
                    "to_address": deposited_transaction.bridge_to_address,
                    "l1_token_address": deposited_transaction.remote_token_address,
                    "l2_token_address": deposited_transaction.local_token_address,
                    "extra_info": deposited_transaction.extra_info,
                    "_type": deposited_transaction.bridge_transaction_type,
                    "target": deposited_transaction.target,
                    "sender": deposited_transaction.sender,
                    "data": deposited_transaction.message,
                }
                for transaction in transactions
                for deposited_transaction in parse_transaction_deposited_event(transaction, self.optimism_portal_proxy)
            ]

            l2_to_l1_withdraw_transactions = [
                {
                    "item": L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN,
                    "msg_hash": proven_transaction.msg_hash,
                    "l1_proven_block_number": proven_transaction.block_number,
                    "l1_proven_block_timestamp": proven_transaction.block_timestamp,
                    "l1_proven_block_hash": proven_transaction.block_hash,
                    "l1_proven_transaction_hash": proven_transaction.transaction_hash,
                    "l1_proven_from_address": proven_transaction.from_address,
                    "l1_proven_to_address": proven_transaction.to_address,
                }
                for transaction in transactions
                for proven_transaction in parse_relayed_message(
                    "WITHDRAWAL_PROVEN_EVENT",
                    transaction,
                    self.optimism_portal_proxy,
                    "withdrawalHash"
                )
            ]

            l2_to_l1_withdraw_transactions += [
                {
                    "item": L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED,
                    "msg_hash": finalized_transaction.msg_hash,
                    "l1_block_number": finalized_transaction.block_number,
                    "l1_block_timestamp": finalized_transaction.block_timestamp,
                    "l1_block_hash": finalized_transaction.block_hash,
                    "l1_transaction_hash": finalized_transaction.transaction_hash,
                    "l1_from_address": finalized_transaction.from_address,
                    "l1_to_address": finalized_transaction.to_address,
                }
                for transaction in transactions
                for finalized_transaction in parse_relayed_message(
                    "WITHDRAWAL_FINALIZED_EVENT",
                    transaction,
                    self.optimism_portal_proxy,
                    "withdrawalHash"
                )
            ]

            result += (l1_to_l2_deposit_transactions + l2_to_l1_withdraw_transactions)

        if self.optimism_portal_proxy:
            op_state_batches = [
                {
                "item": "op_state_batches",
                "batch_index": op_state_batch.batch_index,
                "l1_block_number": op_state_batch.l1_block_number,
                "l1_block_timestamp": op_state_batch.l1_block_timestamp,
                "l1_block_hash": op_state_batch.l1_block_hash,
                "l1_transaction_hash": op_state_batch.l1_transaction_hash,
                "batch_root": op_state_batch.batch_root,
                "end_block_number": op_state_batch.end_block_number,
            }
                for transaction in transactions
                for op_state_batch in parse_propose_l2_output(
                    transaction,
                    self.l2_output_oracle_proxy
                )
            ]
            result += op_state_batches

        return result
