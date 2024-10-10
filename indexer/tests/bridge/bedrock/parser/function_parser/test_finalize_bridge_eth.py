import pytest

from indexer.modules.bridge.bedrock.parser.function_parser import BedRockFunctionCallType


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bedrock_finalize_bridge_eth_decoder():
    from indexer.modules.bridge.bedrock.parser.function_parser.finalize_bridge_eth import decode_function

    bridge_info = decode_function(
        bytearray.fromhex(
            "1635f5fd000000000000000000000000550bf1c892b6a79118a1b20b65c923e8d1e6f715000000000000000000000000550bf1c892b6a79118a1b20b65c923e8d1e6f7150000000000000000000000000000000000000000000000000005789f30f4400000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000"
        )
    )

    assert bridge_info.bridge_from_address == "0x550bf1c892b6a79118a1b20b65c923e8d1e6f715"
    assert bridge_info.bridge_to_address == "0x550bf1c892b6a79118a1b20b65c923e8d1e6f715"
    assert bridge_info.amount == 1540000000000000
    assert bridge_info.remote_function_call_type == BedRockFunctionCallType.BRIDGE_ETH.value
