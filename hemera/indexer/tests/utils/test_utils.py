import pytest

from hemera.common.utils.abi_code_utils import Event, Function, decode_data
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.domain.log import Log
from hemera.indexer.domain.receipt import Receipt
from hemera.indexer.domain.transaction import Transaction


@pytest.mark.indexer
@pytest.mark.indexer_utils
@pytest.mark.serial
def test_decode_data_function():
    data_type = ["uint256"]
    encode_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x0A"
    )

    decoded = decode_data(data_type, encode_data)[0]
    assert decoded == 10

    data_type = ["string"]
    encode_data = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x68\x65\x6c\x6c\x6f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    decoded = decode_data(data_type, encode_data)[0]
    assert decoded == "hello"

    data_type = ["uint256", "string"]
    encode_data = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x68\x65\x6C\x6C\x6F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    decoded = decode_data(data_type, encode_data)
    assert decoded == (10, "hello")

    try:
        data_type = 1155
        encode_data = (
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x0A"
        )

        decode_data(data_type, encode_data)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert str(e) == f"Invalid decode_type: 1155, it should be str or list[str]"

    try:
        data_type = ["uint32", 1155]
        encode_data = (
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x0A"
        )

        decode_data(data_type, encode_data)
    except Exception as e:
        assert isinstance(e, ValueError)
        assert str(e) == f"Invalid decode_type: ['uint32', 1155] is not a List[str]"


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_event_log_decode_sent_message():
    MANTA_PACIFIC_SENT_MESSAGE = Event(
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "address", "name": "target", "type": "address"},
                {"indexed": False, "internalType": "address", "name": "sender", "type": "address"},
                {"indexed": False, "internalType": "bytes", "name": "message", "type": "bytes"},
                {"indexed": False, "internalType": "uint256", "name": "messageNonce", "type": "uint256"},
                {"indexed": False, "internalType": "uint256", "name": "gasLimit", "type": "uint256"},
            ],
            "name": "SentMessage",
            "type": "event",
        }
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
    decoded = MANTA_PACIFIC_SENT_MESSAGE.decode_log(log)
    # {'target': '0x4200000000000000000000000000000000000010', 'sender': '0x3b95bc951ee0f553ba487327278cac44f29715e5', 'message': b'\x165\xf5\xfd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x8d~\xa4\xc6\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 'messageNonce': 1766847064778384329583297500742918515827483896875618958121606201292676996, 'gasLimit': 200000}

    assert decoded["target"] == "0x4200000000000000000000000000000000000010"
    assert decoded["sender"] == "0x3b95bc951ee0f553ba487327278cac44f29715e5"
    assert (
        decoded["message"].hex()
        == "1635f5fd0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f0000000000000000000000005c8680dce97932edf4a14184ce8188ecbfba591f00000000000000000000000000000000000000000000000000038d7ea4c6800000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000000"
    )
    assert decoded["messageNonce"] == 1766847064778384329583297500742918515827483896875618958121606201292676996
    assert decoded["gasLimit"] == 200000


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_function_transaction_decode_deposit_token():
    DEPOSIT_ERC20_TO = Function(
        {
            "inputs": [
                {"internalType": "address", "name": "_l1Token", "type": "address"},
                {"internalType": "address", "name": "_l2Token", "type": "address"},
                {"internalType": "address", "name": "_to", "type": "address"},
                {"internalType": "uint256", "name": "_amount", "type": "uint256"},
                {"internalType": "uint32", "name": "_minGasLimit", "type": "uint32"},
                {"internalType": "bytes", "name": "_extraData", "type": "bytes"},
            ],
            "name": "depositERC20To",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        }
    )

    transaction = Transaction(
        hash="0x2b231d02aef5b4934900e5fd7502620415e8c4945bf59ba329accc0098f7a4a1",
        nonce=4368,
        transaction_index=57,
        from_address="0xA99f61aa6BA5665F62935F7d05Aa4A214a79E388",
        to_address="0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1",
        value=0,
        gas_price=11345504604,
        gas=182273,
        transaction_type=0,
        input="0x838b25200000000000000000000000000001a500a6b18995b03f44bb040a5ffc28e45cb0000000000000000000000000fc2e6e6bcbd49ccf3a5f029c79984372dcbfe527000000000000000000000000a99f61aa6ba5665f62935f7d05aa4a214a79e38800000000000000000000000000000000000000000000002fa08312a91e81460a0000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000b7375706572627269646765000000000000000000000000000000000000000000",
        max_fee_per_gas=0,
        max_priority_fee_per_gas=0,
        block_number=20934172,
        block_hash="0x48d4283d42ddade3a42eeaa2d74a596b2fe280e4e6f9f5c474e7831bc8543601",
        block_timestamp=1728901739,
        receipt=Receipt(
            transaction_hash="0x2b231d02aef5b4934900e5fd7502620415e8c4945bf59ba329accc0098f7a4a1",
            transaction_index=57,
            contract_address="",
            status=1,
            logs=[],
        ),
    )

    decoded = DEPOSIT_ERC20_TO.decode_function_input_data(transaction.input)
    # {'target': '0x4200000000000000000000000000000000000010', 'sender': '0x3b95bc951ee0f553ba487327278cac44f29715e5', 'message': b'\x165\xf5\xfd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\\\x86\x80\xdc\xe9y2\xed\xf4\xa1A\x84\xce\x81\x88\xec\xbf\xbaY\x1f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x8d~\xa4\xc6\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 'messageNonce': 1766847064778384329583297500742918515827483896875618958121606201292676996, 'gasLimit': 200000}

    assert decoded["_l1Token"] == "0x0001a500a6b18995b03f44bb040a5ffc28e45cb0"
    assert decoded["_l2Token"] == "0xfc2e6e6bcbd49ccf3a5f029c79984372dcbfe527"
    assert decoded["_to"] == "0xa99f61aa6ba5665f62935f7d05aa4a214a79e388"
    assert decoded["_amount"] == 878563080249937053194
    assert decoded["_minGasLimit"] == 200000
    assert decoded["_extraData"] == b"superbridge"


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_hex_bytes_convert():
    address = "0x635ba609680c55c3bdd0b3627b4c5db21b13c310"
    bytes_address = b"c[\xa6\th\x0cU\xc3\xbd\xd0\xb3b{L]\xb2\x1b\x13\xc3\x10"

    assert bytes_to_hex_str(bytes_address) == address
    assert hex_str_to_bytes(address) == bytes_address

    address = "635ba609680c55c3bdd0b3627b4c5db21b13c310"
    bytes_address = b"c[\xa6\th\x0cU\xc3\xbd\xd0\xb3b{L]\xb2\x1b\x13\xc3\x10"

    assert bytes_to_hex_str(bytes_address) == "0x" + address
    assert hex_str_to_bytes(address) == bytes_address

    address = "a test"
    try:
        hex_str_to_bytes(address)
    except Exception as e:
        assert str(e) == f"non-hexadecimal number found in fromhex() arg at position 1"
