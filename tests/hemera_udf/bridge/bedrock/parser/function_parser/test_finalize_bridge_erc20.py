import pytest

from hemera_udf.bridge.bedrock.parser.function_parser import BedRockFunctionCallType


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bedrock_finalize_bridge_erc20_decoder():
    from hemera_udf.bridge.bedrock.parser.function_parser.finalize_bridge_erc20 import decode_function

    # BridgeRemoteFunctionCallInfo(bridge_from_address='0xc451b0191351ce308fdfd779d73814c910fc5ecb', bridge_to_address='0xc451b0191351ce308fdfd779d73814c910fc5ecb', local_token_address='0xb73603c5d87fa094b7314c74ace2e64d165016fb', remote_token_address='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', amount=100000000000, extra_info={}, remove_function_call_type=1)
    bridge_info = decode_function(
        bytearray.fromhex(
            "0166a07a000000000000000000000000b73603c5d87fa094b7314c74ace2e64d165016fb000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000000000000000000000000c451b0191351ce308fdfd779d73814c910fc5ecb000000000000000000000000c451b0191351ce308fdfd779d73814c910fc5ecb000000000000000000000000000000000000000000000000000000174876e80000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000000"
        )
    )
    print(bridge_info)

    assert bridge_info.bridge_from_address == "0xc451b0191351ce308fdfd779d73814c910fc5ecb"
    assert bridge_info.bridge_to_address == "0xc451b0191351ce308fdfd779d73814c910fc5ecb"
    assert bridge_info.local_token_address == "0xb73603c5d87fa094b7314c74ace2e64d165016fb"
    assert bridge_info.remote_token_address == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    assert bridge_info.amount == 100000000000
    assert bridge_info.extra_info == {"token": {"type": "ERC20", "amount": 100000000000}}
    assert bridge_info.remote_function_call_type == BedRockFunctionCallType.BRIDGE_ERC20.value
