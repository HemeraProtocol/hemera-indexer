from typing import Any, Dict, List, Optional

from web3 import Web3

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.transaction import Transaction
from hemera_udf.bridge.bedrock.parser.bedrock_bridge_parser import RelayedMessageTransaction
from hemera_udf.bridge.bridge_utils import get_version_and_index_from_nonce
from hemera_udf.bridge.morphl2.abi.event import QueueTransactionEvent, RelayedMessageEvent, SentMessageEvent
from hemera_udf.bridge.morphl2.abi.function import (
    MorphFunctionCollection,
    finalizeBatchDepositERC721Function,
    finalizeBatchDepositERC1155Function,
    finalizeBatchWithdrawERC721Function,
    finalizeBatchWithdrawERC1155Function,
    finalizeDepositERC20Function,
    finalizeDepositERC721Function,
    finalizeDepositERC1155Function,
    finalizeDepositETHFunction,
    finalizeWithdrawERC20Function,
    finalizeWithdrawERC721Function,
    finalizeWithdrawERC1155Function,
    finalizeWithdrawETHFunction,
    relayMessageFunction,
)
from hemera_udf.bridge.morphl2.parser.deposited_transaction import DepositedTransaction


def parse_relayed_message_event(transaction: Transaction, contract_address) -> List[RelayedMessageTransaction]:
    res = []
    for log in transaction.receipt.logs:
        if log.address.lower() == contract_address.lower() and log.topic0 == RelayedMessageEvent.get_signature():
            relayed_message_event = RelayedMessageEvent.decode_log(log)
            msg_hash = relayed_message_event.get("messageHash")

            res.append(
                RelayedMessageTransaction(
                    msg_hash=msg_hash,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                    block_hash=transaction.block_hash,
                    transaction_hash=transaction.hash,
                    from_address=transaction.from_address,
                    to_address=transaction.to_address,
                )
            )
    return res


def parse_sent_message_event(transaction: Transaction, contract_address) -> List[DepositedTransaction]:
    res = []
    for log in transaction.receipt.logs:
        if log.address.lower() == contract_address.lower() and log.topic0 == SentMessageEvent.get_signature():
            sent_message_event = SentMessageEvent.decode_log(log)
            encode_data = relayMessageFunction.encode_function_call_data(
                (
                    sent_message_event.get("sender"),
                    sent_message_event.get("target"),
                    sent_message_event.get("value"),
                    sent_message_event.get("messageNonce"),
                    sent_message_event.get("message"),
                )
            )
            message_hash = Web3.keccak(hexstr=encode_data).hex()
            nonce = sent_message_event.get("messageNonce")
            gas_limit = sent_message_event.get("gasLimit")
            extra_info = {
                "sender": sent_message_event.get("sender"),
                "target": sent_message_event.get("target"),
                "gas_limit": gas_limit,
            }
            res.append(
                parse_withdraw_message(
                    transaction,
                    message_hash,
                    nonce,
                    bytes_to_hex_str(sent_message_event.get("message")),
                    extra_info,
                    sent_message_event.get("sender"),
                    sent_message_event.get("target"),
                )
            )
    return res


def parse_transaction_deposited_event(transaction: Transaction, contract_address) -> List[DepositedTransaction]:
    res = []
    for log in transaction.receipt.logs:
        if log.address.lower() == contract_address.lower() and log.topic0 == QueueTransactionEvent.get_signature():
            transaction_deposited = QueueTransactionEvent.decode_log(log)
            tx_origin = transaction_deposited.get("sender")
            value = transaction_deposited.get("value")
            tx_data = bytes_to_hex_str(transaction_deposited.get("data"))
            gas_limit = transaction_deposited.get("gasLimit")

            tx = relayMessageFunction.decode_function_input_data(tx_data)
            if tx:
                msg_hash = Web3.keccak(hexstr=tx_data).hex()
                target = tx.get("target")
                sender = tx.get("sender")
                msg = bytes_to_hex_str(tx.get("message"))
                nonce = tx.get("messageNonce")
                extra_info = {
                    "sender": sender,
                    "target": target,
                    "gas_limit": gas_limit,
                    "tx_origin": tx_origin,
                }
                res.append(parse_deposit_message(transaction, msg_hash, nonce, msg, extra_info, sender, target))
            else:
                res.append(
                    DepositedTransaction(
                        msg_hash=transaction.hash,
                        block_number=transaction.block_number,
                        block_timestamp=transaction.block_timestamp,
                        block_hash=transaction.block_hash,
                        transaction_hash=transaction.hash,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        bridge_from_address=transaction_deposited.get("sender"),
                        bridge_to_address=transaction_deposited.get("target"),
                        sender=transaction_deposited.get("sender"),
                        target=transaction_deposited.get("target"),
                        amount=value,
                        extra_info={
                            "gas_limit": gas_limit,
                            "tx_origin": tx_origin,
                        },
                        _type=3,
                    )
                )
    return res


withdrawal_functions = MorphFunctionCollection(
    [
        finalizeWithdrawETHFunction,
        finalizeWithdrawERC20Function,
        finalizeWithdrawERC721Function,
        finalizeBatchWithdrawERC721Function,
        finalizeWithdrawERC1155Function,
        finalizeBatchWithdrawERC1155Function,
    ]
)

deposited_functions = MorphFunctionCollection(
    [
        finalizeDepositETHFunction,
        finalizeDepositERC20Function,
        finalizeDepositERC721Function,
        finalizeBatchDepositERC721Function,
        finalizeDepositERC1155Function,
        finalizeBatchDepositERC1155Function,
    ]
)


def parse_withdraw_message(
    transaction: Transaction,
    msg_hash: str,
    nonce: int,
    msg: str,
    extra_info: Optional[Dict[str, Any]] = None,
    sender: Optional[str] = None,
    target: Optional[str] = None,
) -> DepositedTransaction:
    version, index = get_version_and_index_from_nonce(nonce)
    deposited_transaction = withdrawal_functions.decode_function_input_data(msg)
    deposited_transaction.msg_hash = msg_hash
    deposited_transaction.version = version
    deposited_transaction.index = index
    deposited_transaction.block_number = transaction.block_number
    deposited_transaction.block_timestamp = transaction.block_timestamp
    deposited_transaction.block_hash = transaction.block_hash
    deposited_transaction.transaction_hash = transaction.hash
    deposited_transaction.from_address = transaction.from_address
    deposited_transaction.to_address = transaction.to_address
    deposited_transaction.extra_info = deposited_transaction.extra_info or {} | extra_info
    deposited_transaction.sender = sender
    deposited_transaction.target = target

    if deposited_transaction.bridge_from_address is None:
        deposited_transaction.bridge_from_address = transaction.from_address
    if deposited_transaction.bridge_to_address is None:
        deposited_transaction.bridge_to_address = target

    return deposited_transaction


def parse_deposit_message(
    transaction: Transaction,
    msg_hash: str,
    nonce: int,
    msg: str,
    extra_info: Optional[Dict[str, Any]] = None,
    sender: Optional[str] = None,
    target: Optional[str] = None,
) -> DepositedTransaction:
    version, index = get_version_and_index_from_nonce(nonce)
    deposited_transaction = deposited_functions.decode_function_input_data(msg)
    deposited_transaction.msg_hash = msg_hash
    deposited_transaction.version = version
    deposited_transaction.index = index
    deposited_transaction.block_number = transaction.block_number
    deposited_transaction.block_timestamp = transaction.block_timestamp
    deposited_transaction.block_hash = transaction.block_hash
    deposited_transaction.transaction_hash = transaction.hash
    deposited_transaction.from_address = transaction.from_address
    deposited_transaction.to_address = transaction.to_address
    deposited_transaction.extra_info = deposited_transaction.extra_info or {} | extra_info
    deposited_transaction.sender = sender
    deposited_transaction.target = target

    if deposited_transaction.bridge_from_address is None:
        deposited_transaction.bridge_from_address = transaction.from_address
    if deposited_transaction.bridge_to_address is None:
        deposited_transaction.bridge_to_address = target

    return deposited_transaction
