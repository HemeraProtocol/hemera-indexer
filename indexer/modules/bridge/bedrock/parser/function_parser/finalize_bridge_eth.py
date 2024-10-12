import json
from typing import cast

from web3._utils.contracts import decode_transaction_data
from web3.types import ABIFunction

from common.utils.format_utils import bytes_to_hex_str
from indexer.modules.bridge.bedrock.parser.function_parser import (
    BedRockFunctionCallType,
    BridgeRemoteFunctionCallInfo,
    RemoteFunctionCallDecoder,
)
from indexer.utils.abi import function_abi_to_4byte_selector_str

FINALIZE_BRIDGE_ETH = cast(
    ABIFunction,
    json.loads(
        """
        {
            "inputs": [
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
            "name": "finalizeBridgeETH",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
        """
    ),
)


def decode_function(input_data: bytes) -> BridgeRemoteFunctionCallInfo:
    assert len(input_data) >= 4
    print(function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ETH))
    assert function_abi_to_4byte_selector_str(FINALIZE_BRIDGE_ETH) == bytes_to_hex_str(input_data[:4]).lower()

    function_info = decode_transaction_data(FINALIZE_BRIDGE_ETH, input_data.hex())
    if function_info is None:
        raise ValueError("Failed to decode transaction data")

    return BridgeRemoteFunctionCallInfo(
        bridge_from_address=function_info.get("_from"),
        bridge_to_address=function_info.get("_to"),
        local_token_address=None,
        remote_token_address=None,
        amount=function_info.get("_amount"),
        extra_info={},
        remote_function_call_type=BedRockFunctionCallType.BRIDGE_ETH.value,
    )


FINALIZE_BRIDGE_ETH_DECODER = RemoteFunctionCallDecoder(
    function_abi=FINALIZE_BRIDGE_ETH, decode_function=decode_function
)
