import logging
from typing import Any, Callable, Dict, Optional

from eth_typing import ABIFunction

from hemera.common.utils.abi_code_utils import Function, FunctionCollection
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera_udf.bridge.morphl2.parser.deposited_transaction import DepositedTransaction


class MorphFunction(Function):
    def __init__(self, function: ABIFunction, transform_fn: Callable[[Dict[str, Any]], DepositedTransaction]):
        super().__init__(function)
        self.transform_fn = transform_fn


class MorphFunctionCollection(FunctionCollection):
    def __init__(self, functions: list[MorphFunction]):
        super().__init__(functions)

    def decode_function_input_data(self, data: str) -> DepositedTransaction:
        """
        Decodes the input data for a function given its signature.

        :param signature: The signature of the function.
        :type signature: str

        :param data: The input data to decode.
        :type data: str

        :return: A dictionary containing the decoded data, or None if decoding fails.
        :rtype: Optional[Dict[str, Any]]
        """
        signature = data[:10]
        if signature not in self._function_map:
            logging.warning(f"Function signature {signature} not found in function map.")
            return DepositedTransaction()
        function = self._function_map[signature]
        return function.transform_fn(function.decode_function_input_data(data))


relayMessageFunction = Function(
    {
        "type": "function",
        "name": "relayMessage",
        "inputs": [
            {"internalType": "address", "name": "sender", "type": "address"},
            {"internalType": "address", "name": "target", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "uint256", "name": "messageNonce", "type": "uint256"},
            {"internalType": "bytes", "name": "message", "type": "bytes"},
        ],
        "outputs": [],
        "stateMutability": "payable",
        "payable": True,
    }
)

# ETH deposit finalization
finalizeDepositETHFunction = MorphFunction(
    {
        "type": "function",
        "name": "finalizeDepositETH",
        "inputs": [
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "outputs": [],
        "stateMutability": "payable",
        "payable": True,
    },
    lambda x: DepositedTransaction(
        local_token_address=None,
        remote_token_address=None,
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={"data": bytes_to_hex_str(x["_data"])},
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

finalizeDepositERC20Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeDepositERC20",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "outputs": [],
        "stateMutability": "payable",
        "payable": True,
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC20",
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ERC721 deposit finalization
finalizeDepositERC721Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeDepositERC721",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_tokenId", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=1,
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {"token_type": "ERC721", "token_ids": [str(x["_tokenId"])]},
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# Batch ERC721 deposit finalization
finalizeBatchDepositERC721Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeBatchDepositERC721",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256[]", "name": "_tokenIds", "type": "uint256[]"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=len(x["_tokenIds"]),
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC721",
                "token_ids": [str(token_id) for token_id in x["_tokenIds"]],
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ERC1155 deposit finalization
finalizeDepositERC1155Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeDepositERC1155",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {"token_type": "ERC1155", "token_ids": [str(x["_tokenId"])], "amounts": [str(x["_amount"])]},
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# Batch ERC1155 deposit finalization
finalizeBatchDepositERC1155Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeBatchDepositERC1155",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256[]", "name": "_tokenIds", "type": "uint256[]"},
            {"internalType": "uint256[]", "name": "_amounts", "type": "uint256[]"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=sum(x["_amounts"]),
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC1155",
                "token_ids": [str(token_id) for token_id in x["_tokenIds"]],
                "amounts": [str(amount) for amount in x["_amounts"]],
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ETH withdrawal finalization
finalizeWithdrawETHFunction = MorphFunction(
    {
        "type": "function",
        "name": "finalizeWithdrawETH",
        "inputs": [
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "outputs": [],
        "stateMutability": "payable",
        "payable": True,
    },
    lambda x: DepositedTransaction(
        local_token_address=None,
        remote_token_address=None,
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={"data": bytes_to_hex_str(x["_data"])},
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ERC20 withdrawal finalization
finalizeWithdrawERC20Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeWithdrawERC20",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "bytes", "name": "_data", "type": "bytes"},
        ],
        "outputs": [],
        "stateMutability": "payable",
        "payable": True,
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC20",
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ERC721 withdrawal finalization
finalizeWithdrawERC721Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeWithdrawERC721",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_tokenId", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=1,
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {"token_type": "ERC721", "token_ids": [str(x["_tokenId"])]},
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# Batch ERC721 withdrawal finalization
finalizeBatchWithdrawERC721Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeBatchWithdrawERC721",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256[]", "name": "_tokenIds", "type": "uint256[]"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=len(x["_tokenIds"]),
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC721",
                "token_ids": [str(token_id) for token_id in x["_tokenIds"]],
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# ERC1155 withdrawal finalization
finalizeWithdrawERC1155Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeWithdrawERC1155",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=x["_amount"],
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {"token_type": "ERC1155", "token_ids": [str(x["_tokenId"])], "amounts": [str(x["_amount"])]},
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)

# Batch ERC1155 withdrawal finalization
finalizeBatchWithdrawERC1155Function = MorphFunction(
    {
        "type": "function",
        "name": "finalizeBatchWithdrawERC1155",
        "inputs": [
            {"internalType": "address", "name": "_l1Token", "type": "address"},
            {"internalType": "address", "name": "_l2Token", "type": "address"},
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256[]", "name": "_tokenIds", "type": "uint256[]"},
            {"internalType": "uint256[]", "name": "_amounts", "type": "uint256[]"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    lambda x: DepositedTransaction(
        local_token_address=x["_l2Token"],
        remote_token_address=x["_l1Token"],
        bridge_from_address=x["_from"],
        bridge_to_address=x["_to"],
        amount=sum(x["_amounts"]),
        extra_info={
            "data": bytes_to_hex_str(x["_data"]),
            "token": {
                "token_type": "ERC1155",
                "token_ids": [str(token_id) for token_id in x["_tokenIds"]],
                "amounts": [str(amount) for amount in x["_amounts"]],
            },
        },
        _type=1,
        data=bytes_to_hex_str(x["_data"]),
    ),
)
