import pytest

from modules.bridge.bedrock.parser.function_parser import BedRockFunctionCallType


@pytest.mark.util
def test_bedrock_finalize_bridge_erc721_decoder():
    from modules.bridge.bedrock.parser.function_parser.finalize_bridge_erc721 import decode_function

    bridge_info = decode_function(
        bytearray.fromhex(
            "761f4493000000000000000000000000a1a874b461056d7dbe6feb31f2a8c5301a4879dd00000000000000000000000096bfcf262ad1889a20c04b1c22b86157392d23340000000000000000000000007bf925893f7713e00493a67ef0f0127855ad36be0000000000000000000000007bf925893f7713e00493a67ef0f0127855ad36be000000000000000000000000000000000000000000000000000100040000003600000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000"
        )
    )
    # BridgeRemoteFunctionCallInfo(bridge_from_address='0x7bf925893f7713e00493a67ef0f0127855ad36be', bridge_to_address='0x7bf925893f7713e00493a67ef0f0127855ad36be', local_token_address='0xa1a874b461056d7dbe6feb31f2a8c5301a4879dd', remote_token_address='0x96bfcf262ad1889a20c04b1c22b86157392d2334', amount=None, extra_info={'token': {'type': 'ERC721', 'token_ids': [281492156579894]}}, remove_function_call_type=1)

    assert bridge_info.bridge_from_address == "0x7bf925893f7713e00493a67ef0f0127855ad36be"
    assert bridge_info.bridge_to_address == "0x7bf925893f7713e00493a67ef0f0127855ad36be"
    assert bridge_info.local_token_address == "0xa1a874b461056d7dbe6feb31f2a8c5301a4879dd"
    assert bridge_info.remote_token_address == "0x96bfcf262ad1889a20c04b1c22b86157392d2334"

    assert bridge_info.amount == 1
    assert bridge_info.extra_info == {"token": {"type": "ERC721", "token_ids": [281492156579894], "amounts": [1]}}
    assert bridge_info.remote_function_call_type == BedRockFunctionCallType.BRIDGE_ERC721.value
