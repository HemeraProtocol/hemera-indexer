import json
from typing import List, cast

from eth_typing import HexStr
from web3._utils.contracts import decode_transaction_data
from web3.types import ABIEvent, ABIFunction

from indexer.domain.transaction import Transaction
from indexer.modules.bridge.arbitrum.arb_parser import parse_message_delivered, un_marshal_inbox_message_delivered_data
from indexer.modules.custom.deposit_to_l2.domain.token_deposit_transaction import TokenDepositTransaction
from indexer.utils.abi import decode_log, event_log_abi_to_topic, function_abi_to_4byte_selector_str
from indexer.utils.bridge_utils import (
    un_marshal_transaction_deposited_event_version0,
    un_marshal_transaction_deposited_event_version1,
)

ETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

TRANSACTION_DEPOSITED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"version","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"opaqueData","type":"bytes"}],"name":"TransactionDeposited","type":"event"}"""
    ),
)
TRANSACTION_DEPOSITED_EVENT_SIG = event_log_abi_to_topic(TRANSACTION_DEPOSITED_EVENT)

INBOX_MESSAGE_DELIVERED_EVENT = cast(
    ABIEvent,
    json.loads(
        """{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"messageNum","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"InboxMessageDelivered","type":"event"}"""
    ),
)
INBOX_MESSAGE_DELIVERED_EVENT_SIG = event_log_abi_to_topic(INBOX_MESSAGE_DELIVERED_EVENT)


def eth_deposit_parse(transaction: Transaction, chain_mapping: dict, function: ABIFunction) -> TokenDepositTransaction:
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=ETH_ADDRESS,
        value=transaction.value,
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


def usdc_deposit_parse(transaction: Transaction, chain_mapping: dict, function: ABIFunction) -> TokenDepositTransaction:
    decoded_input = decode_transaction_data(function, HexStr(transaction.input))
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=USDC_ADDRESS,
        value=decoded_input["_amount"],
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


def token_deposit_parse(
    transaction: Transaction, chain_mapping: dict, function: ABIFunction
) -> TokenDepositTransaction:
    decoded_input = decode_transaction_data(function, HexStr(transaction.input))
    return TokenDepositTransaction(
        transaction_hash=transaction.hash,
        wallet_address=transaction.from_address,
        chain_id=chain_mapping[transaction.to_address],
        contract_address=transaction.to_address,
        token_address=decoded_input["_l1Token"],
        value=decoded_input["_amount"],
        block_number=transaction.block_number,
        block_timestamp=transaction.block_timestamp,
    )


token_parse_mapping = {
    "eth": eth_deposit_parse,
    "usdc": usdc_deposit_parse,
    "_l1Token": token_deposit_parse,
}


def transaction_deposited_event_log_parse(
    transaction: Transaction, contract: str, chain_mapping: dict
) -> TokenDepositTransaction:
    for log in transaction.receipt.logs:
        if log.address == contract and log.topic0 == TRANSACTION_DEPOSITED_EVENT_SIG:
            log_info = decode_log(TRANSACTION_DEPOSITED_EVENT, log)

            version = log_info["version"]
            opaque_data = log_info["opaqueData"]
            if version == 1:
                mint, value, eth_value, eth_tx_value, gas, is_creation, data = (
                    un_marshal_transaction_deposited_event_version1(opaque_data)
                )
            else:
                mint, value, gas, is_creation, data = un_marshal_transaction_deposited_event_version0(opaque_data)

            if data is None or len(data) == 0:
                return TokenDepositTransaction(
                    transaction_hash=transaction.hash,
                    wallet_address=transaction.from_address,
                    chain_id=chain_mapping[contract],
                    contract_address=transaction.to_address,
                    token_address=ETH_ADDRESS,
                    value=transaction.value,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                )


def inbox_message_delivered_event_log_parse(
    transaction: Transaction, contract: str, chain_mapping: dict
) -> TokenDepositTransaction:
    message_delivered = parse_message_delivered(transaction, [contract])
    kind_mapping = {message.messageIndex: message.kind for message in message_delivered}

    for log in transaction.receipt.logs:
        if log.address == contract and log.topic0 == INBOX_MESSAGE_DELIVERED_EVENT_SIG:
            log_info = decode_log(INBOX_MESSAGE_DELIVERED_EVENT, log)

            message_index = log_info["messageNum"]
            data = log_info["data"]
            kind = kind_mapping[message_index]

            (
                destAddress,
                l2CallValue,
                msgValue,
                gasLimit,
                maxSubmissionCost,
                excessFeeRefundAddress,
                callValueRefundAddress,
                maxFeePerGas,
                dataHex,
                l1TokenId,
                l1TokenAmount,
            ) = un_marshal_inbox_message_delivered_data(kind, data, chain_mapping[contract])

            if kind == 9:
                return TokenDepositTransaction(
                    transaction_hash=transaction.hash,
                    wallet_address=transaction.from_address,
                    chain_id=chain_mapping[contract],
                    contract_address=transaction.to_address,
                    token_address=l1TokenId,
                    value=l1TokenAmount,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                )
            elif kind == 12:
                return TokenDepositTransaction(
                    transaction_hash=transaction.hash,
                    wallet_address=transaction.from_address,
                    chain_id=chain_mapping[transaction.to_address],
                    contract_address=transaction.to_address,
                    token_address=ETH_ADDRESS,
                    value=l1TokenAmount,
                    block_number=transaction.block_number,
                    block_timestamp=transaction.block_timestamp,
                )

            return None


def parse_deposit_transaction_function(
    transactions: List[Transaction],
    contract_set: set,
    chain_mapping: dict,
    sig_function_mapping: dict,
    sig_parse_mapping: dict,
) -> List[TokenDepositTransaction]:
    deposit_tokens = []
    for transaction in transactions:
        if transaction.to_address in contract_set:
            input_sig = transaction.input[0:10]
            if input_sig in sig_function_mapping:
                deposit_transaction = sig_parse_mapping[input_sig](
                    transaction=transaction,
                    chain_mapping=chain_mapping,
                    function=sig_function_mapping[input_sig],
                )
                deposit_tokens.append(deposit_transaction)
    return deposit_tokens


if __name__ == "__main__":
    pass
