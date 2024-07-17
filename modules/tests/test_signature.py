import json
from typing import cast

import pytest
from web3.types import ABIEvent

from modules.bridge.signature import decode_log
from modules.types import Log


@pytest.mark.util
def test_event_log_decode_sent_message():
    MANTA_PACIFIC_SENT_MESSAGE = cast(
        ABIEvent,
        json.loads(
            '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"bytes","name":"message","type":"bytes"},{"indexed":false,"internalType":"uint256","name":"messageNonce","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"gasLimit","type":"uint256"}],"name":"SentMessage","type":"event"}'
        ),
    )

    # Ethereum Mainnet 20266821, 37, 0x2b66fa257d39c63e44daf67a39feaa3c9780d93c8163c937f646eb08ee1f21e9

    log = Log(
        log_index=37,
        address="0x635ba609680c55c3bdd0b3627b4c5db21b13c310",
        data="0x0000000000000000000000003b95bc951ee0f553ba487327278cac44f29715e50000000000000000000000000000000000000000000000000000000000000080000100000000000000000000000000000000000000000000000000000000df840000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f00000000000000000000000000000000000000000000000000038d7ea4c680000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        transaction_hash="0x2b66fa257d39c63e44daf67a39feaa3c9780d93c8163c937f646eb08ee1f21e9",
        transaction_index=0,
        block_timestamp=1720502543,
        block_number=20266821,
        block_hash="0x57e6790144b04dc31ae17601635cbfc5dce540fe23978dff419f470b7f482bdd",
        topic0="0xcb0f7ffd78f9aee47a248fae8db181db6eee833039123e026dcbff529522e52a",
        topic1="0x0000000000000000000000004200000000000000000000000000000000000010",
    )

    decoded = decode_log(MANTA_PACIFIC_SENT_MESSAGE, log)
    # {'target': '0x4200000000000000000000000000000000000010', 'sender': '0x3b95bc951ee0f553ba487327278cac44f29715e5', 'message': b'\x165\xf5\xfd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x8d~\xa4\xc6\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 'messageNonce': 1766847064778384329583297500742918515827483896875618958121606201292676996, 'gasLimit': 200000}

    assert decoded["target"] == "0x4200000000000000000000000000000000000010"
    assert decoded["sender"] == "0x3b95bc951ee0f553ba487327278cac44f29715e5"
    assert (
        decoded["message"].hex()
        == "1635f5fd0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f00000000000000000000000000000000000000000000000000038d7ea4c6800000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000"
    )
    assert decoded["messageNonce"] == 1766847064778384329583297500742918515827483896875618958121606201292676996
    assert decoded["gasLimit"] == 200000
