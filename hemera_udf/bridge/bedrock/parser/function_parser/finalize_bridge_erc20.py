import json
from typing import cast

from eth_typing import ABIFunction
from web3._utils.contracts import decode_transaction_data

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.utils.abi import function_abi_to_4byte_selector_str
from hemera_udf.bridge.bedrock.parser.function_parser import (
    BedRockFunctionCallType,
    BridgeRemoteFunctionCallInfo,
    RemoteFunctionCallDecoder,
)

FINALIZE_BRIDGE_ERC20 = cast(
    ABIFunction,
    json.loads(
        """
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_localToken",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_remoteToken",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_from",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_to",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amount",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "_extraData",
                "type": "bytes"
            }
        ],
        "name": "finalizeBridgeERC20",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
"""
    ),
)


def decode_function(input_data: bytes) -> BridgeRemoteFunctionCallInfo:
    assert len(input_data) >= 4
    print(function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ERC20))
    assert function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ERC20) == bytes_to_hex_str(input_data[:4]).lower()

    function_info = decode_transaction_data(FINALIZE_BRIDGE_ERC20, input_data.hex())
    if function_info is None:
        raise ValueError("Failed to decode transaction data")

    return BridgeRemoteFunctionCallInfo(
        bridge_from_address=function_info.get("_from"),
        bridge_to_address=function_info.get("_to"),
        local_token_address=function_info.get("_localToken"),
        remote_token_address=function_info.get("_remoteToken"),
        amount=function_info.get("_amount"),
        extra_info={
            "token": {
                "type": "ERC20",
                "amount": function_info.get("_amount"),
            }
        },
        remote_function_call_type=BedRockFunctionCallType.BRIDGE_ERC20.value,
    )


FINALIZE_BRIDGE_ERC20_DECODER = RemoteFunctionCallDecoder(
    function_abi=FINALIZE_BRIDGE_ERC20, decode_function=decode_function
)
