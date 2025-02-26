import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

from eth_typing import ABIEvent, ABIFunction
from web3._utils.contracts import decode_transaction_data
from web3.auto import w3

from hemera.common.utils.abi_code_utils import decode_log
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.utils.abi import event_log_abi_to_topic
from hemera_udf.bridge.bedrock.parser.function_parser import (
    BedrockBridgeParser,
    BedRockFunctionCallType,
    BridgeRemoteFunctionCallInfo,
)
from hemera_udf.bridge.bedrock.parser.function_parser.finalize_bridge_erc20 import FINALIZE_BRIDGE_ERC20_DECODER
from hemera_udf.bridge.bedrock.parser.function_parser.finalize_bridge_erc721 import FINALIZE_BRIDGE_ERC721_DECODER
from hemera_udf.bridge.bedrock.parser.function_parser.finalize_bridge_eth import FINALIZE_BRIDGE_ETH_DECODER
from hemera_udf.bridge.bridge_utils import (
    deposit_event_to_op_bedrock_transaction,
    get_version_and_index_from_nonce,
    unmarshal_deposit_version0,
    unmarshal_deposit_version1,
)

bedrockBridgeParser = BedrockBridgeParser(
    [
        FINALIZE_BRIDGE_ETH_DECODER,
        FINALIZE_BRIDGE_ERC20_DECODER,
        FINALIZE_BRIDGE_ERC721_DECODER,
    ]
)


@dataclass
class DepositedTransaction:
    msg_hash: Optional[str]
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
    gas_limit: Optional[int]
    value: Optional[int]
    l2_transaction_hash: Optional[str]
    bridge_transaction_type: int
    message: Optional[str]
    extra_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WithdrawnTransaction:
    withdrawal_hash: Optional[str]
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
    gas_limit: Optional[int]
    value: Optional[int]
    bridge_transaction_type: int
    message: Optional[str]
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


BEDROCK_EVENT_ABIS = {
    "MESSAGE_PASSED_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"gasLimit","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"},{"indexed":false,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"}],"name":"MessagePassed","type":"event"}',
    "TRANSACTION_DEPOSITED_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"version","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"opaqueData","type":"bytes"}],"name":"TransactionDeposited","type":"event"}',
    "RELAYED_MESSAGE_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"msgHash","type":"bytes32"}],"name":"RelayedMessage","type":"event"}',
    "WITHDRAWAL_FINALIZED_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"},{"indexed":false,"internalType":"bool","name":"success","type":"bool"}],"name":"WithdrawalFinalized","type":"event"}',
    "WITHDRAWAL_PROVEN_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"withdrawalHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"WithdrawalProven","type":"event"}',
    "OUTPUT_PROPOSED_EVENT": '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"outputRoot","type":"bytes32"},{"indexed":true,"internalType":"uint256","name":"l2OutputIndex","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"l2BlockNumber","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"l1Timestamp","type":"uint256"}],"name":"OutputProposed","type":"event"}',
}

BEDROCK_EVENT_ABI_MAPPING: Dict[str, ABIEvent] = {
    key: cast(ABIEvent, json.loads(value)) for key, value in BEDROCK_EVENT_ABIS.items()
}

BEDROCK_EVENT_ABI_SIGNATURE_MAPPING: Dict[str, str] = {
    name: event_log_abi_to_topic(abi) for name, abi in BEDROCK_EVENT_ABI_MAPPING.items()
}

RELAY_MESSAGE_FUNCTION = cast(
    ABIFunction,
    json.loads(
        '{"inputs":[{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"address","name":"_sender","type":"address"},{"internalType":"address","name":"_target","type":"address"},{"internalType":"uint256","name":"_value","type":"uint256"},{"internalType":"uint256","name":"_minGasLimit","type":"uint256"},{"internalType":"bytes","name":"_message","type":"bytes"}],"name":"relayMessage","outputs":[],"stateMutability":"payable","type":"function"}'
    ),
)


def parse_transaction_deposited_event(transaction: Transaction, contract_address: str) -> List[DepositedTransaction]:
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
        if (
            log.topic0 == BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["TRANSACTION_DEPOSITED_EVENT"]
            and log.address == contract_address
        ):
            transaction_deposited = decode_log(BEDROCK_EVENT_ABI_MAPPING["TRANSACTION_DEPOSITED_EVENT"], log)

            deposited_version = transaction_deposited["version"]
            tx_origin = transaction_deposited["from"]
            tx_data = transaction_deposited["opaqueData"]
            if deposited_version == 1:
                mint, value, eth_value, eth_tx_value, gas, is_creation, data = unmarshal_deposit_version1(tx_data)
            else:
                mint, value, gas, is_creation, data = unmarshal_deposit_version0(tx_data)
            l2_transaction_hash = deposit_event_to_op_bedrock_transaction(log).hash()
            if data is None or len(data) == 0:
                results.append(
                    DepositedTransaction(
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
                        bridge_transaction_type=BedRockFunctionCallType.NATIVE_BRIDGE_ETH.value,
                        message=None,
                        gas_limit=gas,
                        value=value,
                        extra_info={"gas_limit": gas, "tx_origin": tx_origin},
                    )
                ),
            else:
                relay_message = decode_transaction_data(RELAY_MESSAGE_FUNCTION, data.hex())
                nonce = relay_message["_nonce"]
                sender = relay_message["_sender"]
                target = relay_message["_target"]
                value = relay_message["_value"]
                gas_limit = relay_message["_minGasLimit"]
                message = relay_message["_message"]

                version, index = get_version_and_index_from_nonce(nonce)
                try:
                    bridge_info = bedrockBridgeParser.get_remote_function_call_info(message)
                except ValueError:
                    bridge_info = BridgeRemoteFunctionCallInfo(
                        bridge_from_address=transaction.from_address,
                        bridge_to_address=transaction.to_address,
                        local_token_address=None,
                        remote_token_address=None,
                        amount=value,
                        extra_info={},
                        remote_function_call_type=BedRockFunctionCallType.NORMAL_CROSS_CHAIN_CALL.value,
                    )

                results.append(
                    DepositedTransaction(
                        msg_hash=w3.keccak(hexstr=bytes_to_hex_str(data)).hex(),
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
                        amount=bridge_info.amount,
                        sender=sender,
                        target=target,
                        gas_limit=gas_limit,
                        l2_transaction_hash=l2_transaction_hash,
                        bridge_transaction_type=bridge_info.remote_function_call_type,
                        message=bytes_to_hex_str(message),
                        value=value,
                        extra_info={**bridge_info.extra_info, "tx_origin": tx_origin},
                    )
                )

    return results


def parse_message_passed_event(transaction: Transaction, contract_address: str) -> List[WithdrawnTransaction]:
    """
    Parses the 'MessagePassed' events from transaction logs based on predefined contract addresses.
    This function handles different versions of withdrawal transactions and decodes their data accordingly.

    Parameters:
        transaction (Transaction): The transaction data containing the logs to be parsed.
        contract_address (str): The contract addresses to filter the relevant logs.

    Returns:
        List[WithdrawnTransaction]: A list of WithdrawnTransaction objects containing detailed information about each withdrawal.
    """
    results = []
    logs = transaction.receipt.logs
    for log in logs:
        if (
            log.topic0 == BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["MESSAGE_PASSED_EVENT"]
            and log.address == contract_address
        ):
            message_passed = decode_log(BEDROCK_EVENT_ABI_MAPPING["MESSAGE_PASSED_EVENT"], log)

            withdrawal_hash = message_passed["withdrawalHash"]
            data = message_passed["data"]
            nonce = message_passed["nonce"]

            relay_message = decode_transaction_data(RELAY_MESSAGE_FUNCTION, data.hex())

            sender = relay_message["_sender"]
            target = relay_message["_target"]
            value = relay_message["_value"]
            gas_limit = relay_message["_minGasLimit"]
            message = relay_message["_message"]

            version, index = get_version_and_index_from_nonce(nonce)
            try:
                bridge_info = bedrockBridgeParser.get_remote_function_call_info(message)
            except ValueError:
                bridge_info = BridgeRemoteFunctionCallInfo(
                    bridge_from_address=transaction.from_address,
                    bridge_to_address=transaction.to_address,
                    local_token_address=None,
                    remote_token_address=None,
                    amount=value,
                    extra_info={},
                    remote_function_call_type=BedRockFunctionCallType.NORMAL_CROSS_CHAIN_CALL.value,
                )

            results.append(
                WithdrawnTransaction(
                    withdrawal_hash=bytes_to_hex_str(withdrawal_hash),
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
                    amount=bridge_info.amount,
                    value=value,
                    sender=sender,
                    target=target,
                    gas_limit=gas_limit,
                    bridge_transaction_type=bridge_info.remote_function_call_type,
                    message=bytes_to_hex_str(message),
                    extra_info={**bridge_info.extra_info},
                )
            )

    return results


def parse_relayed_message(
    abi_event_name: str, transaction: Transaction, contract_address: str, msg_filed_name
) -> List[RelayedMessageTransaction]:
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
        if (
            log.topic0 is not None
            and log.topic0 == BEDROCK_EVENT_ABI_SIGNATURE_MAPPING[abi_event_name]
            and log.address == contract_address
        ):
            relayed_message = decode_log(BEDROCK_EVENT_ABI_MAPPING[abi_event_name], log)
            msg_hash = relayed_message[msg_filed_name]
            results.append(
                RelayedMessageTransaction(
                    msg_hash=bytes_to_hex_str(msg_hash),
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                    block_hash=transaction.block_hash,
                    transaction_hash=transaction.hash,
                    from_address=transaction.from_address,
                    to_address=transaction.to_address,
                )
            )

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
        if (
            log.topic0 is not None
            and log.topic0 == BEDROCK_EVENT_ABI_SIGNATURE_MAPPING["OUTPUT_PROPOSED_EVENT"]
            and log.address == contract_address
        ):
            output_proposed = decode_log(BEDROCK_EVENT_ABI_MAPPING["OUTPUT_PROPOSED_EVENT"], log)
            results.append(
                OpStateBatch(
                    batch_index=output_proposed["l2OutputIndex"],
                    l1_block_number=transaction.block_number,
                    l1_block_timestamp=transaction.block_timestamp,
                    l1_block_hash=transaction.block_hash,
                    l1_transaction_hash=transaction.hash,
                    end_block_number=output_proposed["l2BlockNumber"],
                    batch_root=bytes_to_hex_str(output_proposed["outputRoot"]),
                )
            )
    return results
