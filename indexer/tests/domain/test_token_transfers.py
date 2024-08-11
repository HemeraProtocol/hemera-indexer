import pytest

from indexer.domain.log import Log
from indexer.domain.token_transfer import extract_transfer_from_log
from indexer.utils.utils import ZERO_ADDRESS


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_erc20_token_transfer():
    log = Log(
        log_index=30,
        address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        data="0x000000000000000000000000000000000000000000000000004fcac4d4c7af2e",
        transaction_hash="0xa997e7b311a972a5a1f6f99bee98eaca3f719c549f2a756e0a74d76ed6061028",
        transaction_index=39,
        block_timestamp=1722382175,
        block_number=20425048,
        block_hash="0x6db7768a30446e0a6d00c624d4ec1d17e5eabd8b4cb464396900b967fd9a6058",
        topic0="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        topic1="0x00000000000000000000000086d169ffe8f1ac313abea5fa64aad51725ceaf32",
        topic2="0x00000000000000000000000042619f1eb89b993f7f5193de6ab1423a703fc344",
    )
    token_transfers = extract_transfer_from_log(log)

    assert len(token_transfers) == 1
    token_transfer = token_transfers[0]

    assert token_transfer.transaction_hash == "0xa997e7b311a972a5a1f6f99bee98eaca3f719c549f2a756e0a74d76ed6061028"
    assert token_transfer.log_index == 30
    assert token_transfer.from_address == "0x86d169ffe8f1ac313abea5fa64aad51725ceaf32"
    assert token_transfer.to_address == "0x42619f1eb89b993f7f5193de6ab1423a703fc344"
    assert token_transfer.token_id is None
    assert token_transfer.value == 22459469892398894
    assert token_transfer.token_type == "ERC20"
    assert token_transfer.token_address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    assert token_transfer.block_number == 20425048
    assert token_transfer.block_hash == "0x6db7768a30446e0a6d00c624d4ec1d17e5eabd8b4cb464396900b967fd9a6058"
    assert token_transfer.block_timestamp == 1722382175


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_erc20_token_deposit():
    log = Log(
        log_index=29,
        address="0x6b175474e89094c44da98b954eedeac495271d0f",
        data="0x000000000000000000000000000000000000000000000000004fcac4d4c7af2e",
        transaction_hash="0xa997e7b311a972a5a1f6f99bee98eaca3f719c549f2a756e0a74d76ed6061028",
        transaction_index=39,
        block_timestamp=1722382175,
        block_number=20425048,
        block_hash="0x6db7768a30446e0a6d00c624d4ec1d17e5eabd8b4cb464396900b967fd9a6058",
        topic0="0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c",
        topic1="0x00000000000000000000000086d169ffe8f1ac313abea5fa64aad51725ceaf32",
    )
    token_transfers = extract_transfer_from_log(log)

    assert len(token_transfers) == 0
    # token_transfer = token_transfers[0]

    # assert token_transfer.transaction_hash == "0xa997e7b311a972a5a1f6f99bee98eaca3f719c549f2a756e0a74d76ed6061028"
    # assert token_transfer.log_index == 29
    # assert token_transfer.from_address == ZERO_ADDRESS
    # assert token_transfer.to_address == "0x86d169ffe8f1ac313abea5fa64aad51725ceaf32"
    # assert token_transfer.token_id is None
    # assert token_transfer.value == 22459469892398894
    # assert token_transfer.token_type == "ERC20"
    # assert token_transfer.token_address == "0x6b175474e89094c44da98b954eedeac495271d0f"
    # assert token_transfer.block_number == 20425048
    # assert token_transfer.block_hash == "0x6db7768a30446e0a6d00c624d4ec1d17e5eabd8b4cb464396900b967fd9a6058"
    # assert token_transfer.block_timestamp == 1722382175


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_erc20_token_withdraw():
    log = Log(
        log_index=438,
        address="0x6b175474e89094c44da98b954eedeac495271d0f",
        data="0x00000000000000000000000000000000000000000000000000b13a485de9b6e5",
        transaction_hash="0x01bf14796bb1c6ba3c5fdc599ddad343b04222e252e77d474aa617943bb3d69b",
        transaction_index=172,
        block_timestamp=1722411671,
        block_number=20425106,
        block_hash="0x4ce31db1374c8b6e3065b03daa9a26d545f7c0c76321e255b9b48ec567ec0f2f",
        topic0="0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65",
        topic1="0x0000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d",
    )

    token_transfers = extract_transfer_from_log(log)

    assert len(token_transfers) == 0
    # token_transfer = token_transfers[0]

    # assert token_transfer.transaction_hash == "0x01bf14796bb1c6ba3c5fdc599ddad343b04222e252e77d474aa617943bb3d69b"
    # assert token_transfer.log_index == 438
    # assert token_transfer.from_address == "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
    # assert token_transfer.to_address == ZERO_ADDRESS
    # assert token_transfer.token_id is None
    # assert token_transfer.value == 49885153365440229
    # assert token_transfer.token_type == "ERC20"
    # assert token_transfer.token_address == "0x6b175474e89094c44da98b954eedeac495271d0f"
    # assert token_transfer.block_number == 20425106
    # assert token_transfer.block_hash == "0x4ce31db1374c8b6e3065b03daa9a26d545f7c0c76321e255b9b48ec567ec0f2f"
    # assert token_transfer.block_timestamp == 1722411671


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_erc1155_token_transfer():
    log = Log(
        log_index=182,
        address="0x6e3bc168f6260ff54257ae4b56449efd7afd5934",
        data="0x0000000000000000000000000000000000000000000000000000000005fa75450000000000000000000000000000000000000000000000000000000000000001",
        transaction_hash="0xe31805a3367623df0cf192d4dd4f06361ac2b9a4481cdbde6eb3c2fe4cde1386",
        transaction_index=116,
        block_timestamp=1722394859,
        block_number=20423709,
        block_hash="0x54364a45a1742b14e3b54f8705c5f01d39884af12c6d4cc8350ed9d83b0a5d8b",
        topic0="0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62",
        topic1="0x0000000000000000000000001e0049783f008a0085193e00003d00cd54003c71",
        topic2="0x0000000000000000000000007d791ddc3ca93bb7b88e6e83cbdae9bb0cdfc4c8",
        topic3="0x0000000000000000000000002df85a7ddbbce79f86275d09c2f613f332986427",
    )

    token_transfers = extract_transfer_from_log(log)
    assert len(token_transfers) == 1
    token_transfer = token_transfers[0]

    assert token_transfer.transaction_hash == "0xe31805a3367623df0cf192d4dd4f06361ac2b9a4481cdbde6eb3c2fe4cde1386"
    assert token_transfer.log_index == 182
    assert token_transfer.from_address == "0x7d791ddc3ca93bb7b88e6e83cbdae9bb0cdfc4c8"
    assert token_transfer.to_address == "0x2df85a7ddbbce79f86275d09c2f613f332986427"
    assert token_transfer.token_id == 100300101
    assert token_transfer.value == 1
    assert token_transfer.token_type == "ERC1155"
    assert token_transfer.token_address == "0x6e3bc168f6260ff54257ae4b56449efd7afd5934"
    assert token_transfer.block_number == 20423709
    assert token_transfer.block_hash == "0x54364a45a1742b14e3b54f8705c5f01d39884af12c6d4cc8350ed9d83b0a5d8b"
    assert token_transfer.block_timestamp == 1722394859


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_erc1155_batch_token_transfer():
    log = Log(
        log_index=196,
        address="0xb23d80f5fefcddaa212212f028021b41ded428cf",
        data="0x0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000005fa74e600000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001",
        transaction_hash="0xc2f4b91f7ffeff570529fe837e4d699e44413113b88c6b388a6f068320e3cb9a",
        transaction_index=94,
        block_timestamp=1698823775,
        block_number=18475773,
        block_hash="0x54364a45a1742b14e3b54f8705c5f01d39884af12c6d4cc8350ed9d83b0a5d8b",
        topic0="0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb",
        topic1="0x0000000000000000000000005745411fe0d60dcd64177b4efdc2455d7bb0d0c5",
        topic2="0x0000000000000000000000000000000000000000000000000000000000000000",
        topic3="0x00000000000000000000000006b2f8a86698b0da405a55af456495be2aff5461",
    )
    token_transfers = extract_transfer_from_log(log)
    assert len(token_transfers) == 1
    token_transfer = token_transfers[0]

    assert token_transfer.transaction_hash == "0xc2f4b91f7ffeff570529fe837e4d699e44413113b88c6b388a6f068320e3cb9a"
    assert token_transfer.log_index == 196
    assert token_transfer.from_address == ZERO_ADDRESS
    assert token_transfer.to_address == "0x06b2f8a86698b0da405a55af456495be2aff5461"
    assert token_transfer.token_id == 100300006
    assert token_transfer.value == 1
    assert token_transfer.token_type == "ERC1155"
    assert token_transfer.token_address == "0xb23d80f5fefcddaa212212f028021b41ded428cf"
    assert token_transfer.block_number == 18475773
    assert token_transfer.block_hash == "0x54364a45a1742b14e3b54f8705c5f01d39884af12c6d4cc8350ed9d83b0a5d8b"
    assert token_transfer.block_timestamp == 1698823775
