import json
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, cast

from web3._utils.contracts import decode_transaction_data
from web3.auto import w3
from web3.types import ABIEvent, ABIFunction

from extractor.bridge.bedrock.op_bedrock_deposit_transaction import deposit_event_to_op_bedrock_transaction
from extractor.bridge.bedrock.function_parser import BedrockBridgeParser, BridgeRemoteFunctionCallInfo
from extractor.bridge.bedrock.function_parser.finalize_bridge_erc20 import FINALIZE_BRIDGE_ERC20_DECODER
from extractor.bridge.bedrock.function_parser.finalize_bridge_erc721 import FINALIZE_BRIDGE_ERC721_DECODER
from extractor.bridge.bedrock.function_parser.finalize_bridge_eth import FINALIZE_BRIDGE_ETH_DECODER
from extractor.bridge.utils import unmarshal_deposit_version1, unmarshal_deposit_version0, \
    get_version_and_index_from_nonce
from extractor.signature import event_log_abi_to_topic, decode_log, bytes_to_hex_str
from extractor.types import Transaction

bedrockBridgeParser = BedrockBridgeParser([
    FINALIZE_BRIDGE_ETH_DECODER, FINALIZE_BRIDGE_ERC20_DECODER, FINALIZE_BRIDGE_ERC721_DECODER
])


@dataclass
class DepositedTransaction:
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
    sender: str
    target: str
    l2_transaction_hash: Optional[str]
    bridge_transaction_type: int
    data: Optional[str]
    extra_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpStateBatch:
    batch_index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    end_block_number: int
    batch_root: str


@dataclass
class RelayedMessageTransaction:
    msg_hash: str
    block_number: int
    block_timestamp: int
    block_hash: str
    transaction_hash: str
    from_address: str
    to_address: str


MESSAGE_PASSED_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"gasLimit","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"},{"indexed":false,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"}],"name":"MessagePassed","type":"event"}'))

TRANSACTION_DEPOSITED_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"version","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"opaqueData","type":"bytes"}],"name":"TransactionDeposited","type":"event"}'
))

RELAYED_MESSAGE_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"msgHash","type":"bytes32"}],"name":"RelayedMessage","type":"event"}'
))

WITHDRAWAL_FINALIZED_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"},{"indexed":false,"internalType":"bool","name":"success","type":"bool"}],"name":"WithdrawalFinalized","type":"event"}'
))

WITHDRAWAL_PROVEN_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"WithdrawalProven","type":"event"}'
))

RELAY_MESSAGE_FUNCTION = cast(ABIFunction, json.loads(
    '{"inputs":[{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"address","name":"_sender","type":"address"},{"internalType":"address","name":"_target","type":"address"},{"internalType":"uint256","name":"_value","type":"uint256"},{"internalType":"uint256","name":"_minGasLimit","type":"uint256"},{"internalType":"bytes","name":"_message","type":"bytes"}],"name":"relayMessage","outputs":[],"stateMutability":"payable","type":"function"}'
))

OUTPUT_PROPOSED_EVENT = cast(ABIEvent, json.loads(
    '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"outputRoot","type":"bytes32"},{"indexed":true,"internalType":"uint256","name":"l2OutputIndex","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"l2BlockNumber","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"l1Timestamp","type":"uint256"}],"name":"OutputProposed","type":"event"}'
))


def parse_transaction_deposited_event(transaction: Transaction, contract_address: str) -> List[
    DepositedTransaction]:
    """
    Parses the 'TransactionDeposited' events from transaction logs based on predefined contract addresses.
    This function handles different versions of deposited transactions and decodes their data accordingly.

    Parameters:
    transaction (Transaction): The transaction data containing the logs to be parsed.
    contract_address (str): The contract addresses to filter the relevant logs.

    Returns:
    List[DepositedTransaction]: A list of DepositedTransaction objects containing detailed information about each deposit.
    """

    results = []
    logs = transaction.receipt.logs
    for log in logs:
        if log.topic0 == event_log_abi_to_topic(TRANSACTION_DEPOSITED_EVENT) and log.address == contract_address:
            transaction_deposited = decode_log(TRANSACTION_DEPOSITED_EVENT, log)

            deposited_version = transaction_deposited['version']
            tx_origin = transaction_deposited['from']
            tx_data = transaction_deposited['opaqueData']
            if deposited_version == 1:
                mint, value, eth_value, eth_tx_value, gas, is_creation, data = unmarshal_deposit_version1(tx_data)
            else:
                mint, value, gas, is_creation, data = unmarshal_deposit_version0(tx_data)
            l2_transaction_hash = deposit_event_to_op_bedrock_transaction(log).encode().hash()
            if tx_data is None or len(tx_data) == 0:
                results.append(DepositedTransaction(
                    msg_hash=l2_transaction_hash,
                    version=None,
                    index=None,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                    block_hash=transaction.block_hash,
                    transaction_hash=transaction.hash,
                    from_address=transaction.from_address,
                    to_address=transaction.to_address,
                    local_token_address=None,
                    remote_token_address=None,
                    bridge_from_address=transaction.from_address,
                    bridge_to_address=transaction.from_address,
                    amount=value,
                    sender=transaction.from_address,
                    target=transaction.from_address,
                    l2_transaction_hash=l2_transaction_hash,
                    bridge_transaction_type=0xFF,
                    data=None,
                    extra_info={"gas_limit": gas, "tx_origin": tx_origin}
                )),
            else:
                relay_message = decode_transaction_data(RELAY_MESSAGE_FUNCTION, tx_data)
                nonce = relay_message["_nonce"]
                sender = relay_message["_sender"]
                target = relay_message["_target"]
                value = relay_message["_value"]
                gas_limit = relay_message["_minGasLimit"]
                data = relay_message["_message"]

                version, index = get_version_and_index_from_nonce(nonce)
                try:
                    bridge_info = bedrockBridgeParser.get_remote_function_call_info(data)
                except ValueError:
                    bridge_info = BridgeRemoteFunctionCallInfo(
                        bridge_from_address=transaction.from_address,
                        bridge_to_address=transaction.to_address,
                        local_token_address=None,
                        remote_token_address=None,
                        amount=value,
                        extra_info={},
                        remove_function_call_type=0
                    )

                results.append(DepositedTransaction(
                    msg_hash=bytes_to_hex_str(w3.keccak(hexstr=bytes_to_hex_str(tx_data))),
                    version=version,
                    index=index,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                    block_hash=transaction.block_hash,
                    transaction_hash=transaction.hash,
                    from_address=transaction.from_address,
                    to_address=transaction.to_address,
                    local_token_address=bridge_info.local_token_address,
                    remote_token_address=bridge_info.remote_token_address,
                    bridge_from_address=bridge_info.bridge_from_address,
                    bridge_to_address=bridge_info.bridge_to_address,
                    amount=value,
                    sender=sender,
                    target=target,
                    l2_transaction_hash=l2_transaction_hash,
                    bridge_transaction_type=bridge_info.remove_function_call_type,
                    data=data,
                    extra_info={**bridge_info.extra_info, "gas_limit": gas_limit, "tx_origin": tx_origin}
                ))

    return results


def parse_relayed_message(abi_event: ABIEvent, transaction: Transaction, contract_address: str, msg_filed_name) -> List[
    RelayedMessageTransaction]:
    """
    Parses and processes relayed message events, including the following cases:
    - RelayedMessage on L2: Relayed message event on Layer 2
    - WithdrawalProven on L1: Proven withdrawal event on Layer 1
    - WithdrawalFinalized on L2: Finalized withdrawal event on Layer 2

    Parameters:
    abi_event (ABIEvent): The ABI event object containing detailed event information.
    transaction (Transaction): The transaction object associated with the event.
    contract_address (str): The contract addresses to filter the relevant logs.
    msg_filed_name (str): The field name in the message to be processed.

    Returns:
    List[RelayedMessageTransaction]: A list of parsed relayed message transactions.
    """

    results = []
    logs = transaction.receipt.logs
    for log in logs:
        if log.topic0 is not None and log.topic0 == event_log_abi_to_topic(
                abi_event) and log.address == contract_address:
            relayed_message = decode_log(abi_event, log)
            msg_hash = relayed_message[msg_filed_name]
            results.append(RelayedMessageTransaction(
                msg_hash=bytes_to_hex_str(msg_hash),
                block_number=transaction.block_number,
                block_timestamp=transaction.block_timestamp,
                block_hash=transaction.block_hash,
                transaction_hash=transaction.hash,
                from_address=transaction.from_address,
                to_address=transaction.to_address
            ))

    return results


def parse_propose_l2_output(transaction: Transaction, contract_address: str) -> List[OpStateBatch]:
    """
    Parses proposed outputs for Layer 2 operations, primarily focusing on state batches that may include multiple transactions.
    This function can be expanded to parse and handle specific types of state updates or batch operations from Layer 1 to Layer 2.

    Parameters:
    transaction (Transaction): The transaction data containing the logs to be parsed.
    contract_address (str): The contract addresses to filter the relevant logs.

    Returns:
    List[RelayedMessageTransaction]: A list of transactions indicating state changes or updates in L2 as proposed from L1.
    """

    results = []
    logs = transaction.receipt.logs
    for log in logs:
        if log.topic0 is not None and log.topic0 == event_log_abi_to_topic(
                OUTPUT_PROPOSED_EVENT) and log.address == contract_address:
            output_proposed = decode_log(OUTPUT_PROPOSED_EVENT, log)
            results.append(OpStateBatch(
                batch_index=output_proposed["l2OutputIndex"],
                l1_block_number=transaction.block_number,
                l1_block_timestamp=transaction.block_timestamp,
                l1_block_hash=transaction.block_hash,
                l1_transaction_hash=transaction.hash,
                end_block_number=output_proposed["l2BlockNumber"],
                batch_root=bytes_to_hex_str(output_proposed["outputRoot"])
            ))
    return results
