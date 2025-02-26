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

FINALIZE_BRIDGE_ERC721 = cast(
    ABIFunction,
    json.loads(
        """
    {
        "type": "function",
        "name": "finalizeBridgeERC721",
        "inputs": [
            {
                "name": "_localToken",
                "type": "address",
                "internalType": "address"
            },
            {
                "name": "_remoteToken",
                "type": "address",
                "internalType": "address"
            },
            {
                "name": "_from",
                "type": "address",
                "internalType": "address"
            },
            {
                "name": "_to",
                "type": "address",
                "internalType": "address"
            },
            {
                "name": "_tokenId",
                "type": "uint256",
                "internalType": "uint256"
            },
            {
                "name": "_extraData",
                "type": "bytes",
                "internalType": "bytes"
            }
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    }
"""
    ),
)


def decode_function(input_data: bytes) -> BridgeRemoteFunctionCallInfo:
    assert len(input_data) >= 4
    print(function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ERC721))
    assert function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ERC721) == bytes_to_hex_str(input_data[:4])

    function_info = decode_transaction_data(FINALIZE_BRIDGE_ERC721, input_data.hex())
    if function_info is None:
        raise ValueError("Failed to decode transaction data")

    return BridgeRemoteFunctionCallInfo(
        bridge_from_address=function_info.get("_from"),
        bridge_to_address=function_info.get("_to"),
        local_token_address=function_info.get("_localToken"),
        remote_token_address=function_info.get("_remoteToken"),
        amount=1,
        extra_info={
            "token": {
                "type": "ERC721",
                "token_ids": [function_info.get("_tokenId")],
                "amounts": [1],
            }
        },
        remote_function_call_type=BedRockFunctionCallType.BRIDGE_ERC721.value,
    )


FINALIZE_BRIDGE_ERC721_DECODER = RemoteFunctionCallDecoder(
    function_abi=FINALIZE_BRIDGE_ERC721, decode_function=decode_function
)
