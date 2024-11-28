import pytest

from custom_jobs.bridge.bedrock.parser.bedrock_bridge_parser import (
    parse_message_passed_event,
    parse_transaction_deposited_event,
)
from custom_jobs.bridge.bedrock.parser.function_parser import BedRockFunctionCallType
from indexer.tests.json_rpc_to_dataclass import get_transaction_from_rpc

DEFAULT_ETHEREUM_RPC = "https://ethereum-rpc.publicnode.com"
DEFAULT_OPTIMISM_RPC = "https://optimism-rpc.publicnode.com"


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_manta_pacific_deposit_eth():
    # Ethereum Mainnet 20273058, 188, 0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243
    # https://manta.socialscan.io/tx/0xe579c588d55fea0b4fcf50058fba654b5ef9f7770c79d946e8e673d18a550cd7#eventlog
    # https://etherscan.io/tx/0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243",
    )
    deposit_transactions = parse_transaction_deposited_event(transaction, "0x9168765ee952de7c6f8fc6fad5ec209b960b7622")

    assert deposit_transactions is not None
    assert len(deposit_transactions) == 1

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0x2dab139e9279c94e88e0bd9404a16317745eb97cdbe3707eacef53e8a530ed08"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 57230
    assert deposit_transaction.block_number == 20273058
    assert deposit_transaction.block_timestamp == 1720577867
    assert deposit_transaction.block_hash == "0x6d5644ab134fe01595e3e0628fe4945a47666f7dba251c2258b99ed7b1705585"
    assert deposit_transaction.transaction_hash == "0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243"
    assert deposit_transaction.from_address == "0xbe821f7f9c1c762a15a8073c2e4ea6cfe07a4752"
    assert deposit_transaction.to_address == "0x3b95bc951ee0f553ba487327278cac44f29715e5"
    assert deposit_transaction.local_token_address is None
    assert deposit_transaction.remote_token_address is None

    assert (
        deposit_transaction.l2_transaction_hash == "0xe579c588d55fea0b4fcf50058fba654b5ef9f7770c79d946e8e673d18a550cd7"
    )

    assert deposit_transaction.bridge_from_address == "0xbe821f7f9c1c762a15a8073c2e4ea6cfe07a4752"
    assert deposit_transaction.bridge_to_address == "0xbe821f7f9c1c762a15a8073c2e4ea6cfe07a4752"

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.BRIDGE_ETH.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_manta_pacific_deposit_erc20():
    # Ethereum Mainnet 20262131, 184, 0xbcc8dc6933ea4fdfe745d95518af379619e9eac6b1533955f7b164fc80852ca2
    # https://manta.socialscan.io/tx/0x570412db65e763883b9c7e5e770c5477acca0b82873336dcb150ec982400d122
    # https://etherscan.io/tx/0xbcc8dc6933ea4fdfe745d95518af379619e9eac6b1533955f7b164fc80852ca2#eventlog
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0xbcc8dc6933ea4fdfe745d95518af379619e9eac6b1533955f7b164fc80852ca2",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0x9168765ee952de7c6f8fc6fad5ec209b960b7622")

    assert deposit_transactions is not None
    assert len(deposit_transactions) == 1

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0xb072276416696749400230fd59d43c72cf373b21175127d15f7956bbd128237c"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 57211
    assert deposit_transaction.block_number == 20262131
    assert deposit_transaction.block_timestamp == 1720445795
    assert deposit_transaction.block_hash == "0x8f92aba1ceea9d71567b80a65a020ad97d26c60373935dc27708086ba0e0c4d9"
    assert deposit_transaction.transaction_hash == "0xbcc8dc6933ea4fdfe745d95518af379619e9eac6b1533955f7b164fc80852ca2"
    assert deposit_transaction.from_address == "0xc451b0191351ce308fdfd779d73814c910fc5ecb"
    assert deposit_transaction.to_address == "0x3b95bc951ee0f553ba487327278cac44f29715e5"

    assert deposit_transaction.local_token_address == "0xb73603c5d87fa094b7314c74ace2e64d165016fb"
    assert deposit_transaction.remote_token_address == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    assert (
        deposit_transaction.l2_transaction_hash == "0x570412db65e763883b9c7e5e770c5477acca0b82873336dcb150ec982400d122"
    )

    assert deposit_transaction.bridge_from_address == "0xc451b0191351ce308fdfd779d73814c910fc5ecb"
    assert deposit_transaction.bridge_to_address == "0xc451b0191351ce308fdfd779d73814c910fc5ecb"

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.BRIDGE_ERC20.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_remote_call():
    # Ethereum Mainnet 20274905, 555, 0x860d146dc16026deadd4225b894a2438ce3fa54afb55b0f534be13b7bd238224
    # https://etherscan.io/tx/0x860d146dc16026deadd4225b894a2438ce3fa54afb55b0f534be13b7bd238224#eventlog
    # https://optimistic.etherscan.io/tx/0xfb206642c2bfa141695447eac09f8e1c2000fa73a564f0f676157b928b7a7ded
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0x860d146dc16026deadd4225b894a2438ce3fa54afb55b0f534be13b7bd238224",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0xbeb5fc579115071764c7423a4f12edde41f106ed")

    assert deposit_transactions is not None
    assert len(deposit_transactions) == 1

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0x71afdf6b1f4d51568a124a49fcdfb9e18d3d4d52a0e952e7ff4ff32a0ac1bd37"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 123765
    assert deposit_transaction.block_number == 20274905
    assert deposit_transaction.block_timestamp == 1720600115
    assert deposit_transaction.block_hash == "0x7d6a5f75259e030675dc3d1dbd1c749f2d95133054405b7f37bcc91d9fdb0392"
    assert deposit_transaction.transaction_hash == "0x860d146dc16026deadd4225b894a2438ce3fa54afb55b0f534be13b7bd238224"
    assert deposit_transaction.from_address == "0x1eda738c90fb3f80067a2e420a1e2f81b75ecaf5"
    assert deposit_transaction.to_address == "0xa6d85f3b3be6ff6dc52c3aabe9a35d0ce252b79f"

    assert deposit_transaction.local_token_address is None
    assert deposit_transaction.remote_token_address is None

    assert (
        deposit_transaction.l2_transaction_hash == "0xfb206642c2bfa141695447eac09f8e1c2000fa73a564f0f676157b928b7a7ded"
    )

    assert deposit_transaction.bridge_from_address == "0x1eda738c90fb3f80067a2e420a1e2f81b75ecaf5"
    assert deposit_transaction.bridge_to_address == "0xa6d85f3b3be6ff6dc52c3aabe9a35d0ce252b79f"

    assert deposit_transaction.amount == 0

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.NORMAL_CROSS_CHAIN_CALL.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_deposit_eth():
    # Ethereum Mainnet 20273626, 138, 0x74ff0a208a0b86362df9c290b30a98752b2681ccb634690a17ddaf98d488fb2a
    # https://etherscan.io/tx/0x74ff0a208a0b86362df9c290b30a98752b2681ccb634690a17ddaf98d488fb2a
    # https://optimistic.etherscan.io/tx/0x10235d4c3a99666bf5dd90cb8daa8afde018cac8bcf88fd69acbe5f8d8295bb1

    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0x74ff0a208a0b86362df9c290b30a98752b2681ccb634690a17ddaf98d488fb2a",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0xbeb5fc579115071764c7423a4f12edde41f106ed")

    assert deposit_transactions is not None

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0xf1bdd4168d1d7ed89140092c13e56631a109af1fae0518e523c733c3f976d7d9"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 123728
    assert deposit_transaction.block_number == 20273626
    assert deposit_transaction.block_timestamp == 1720584719
    assert deposit_transaction.block_hash == "0x7e9bf971c54c3985885f9744752031e1eba5483535e3fa0e2b20ba9f68283235"
    assert deposit_transaction.transaction_hash == "0x74ff0a208a0b86362df9c290b30a98752b2681ccb634690a17ddaf98d488fb2a"
    assert deposit_transaction.from_address == "0xa62693542764185c01ea0e34f96ece0fa32dcbf7"
    assert deposit_transaction.to_address == "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"

    assert deposit_transaction.local_token_address is None
    assert deposit_transaction.remote_token_address is None

    assert (
        deposit_transaction.l2_transaction_hash == "0x10235d4c3a99666bf5dd90cb8daa8afde018cac8bcf88fd69acbe5f8d8295bb1"
    )

    assert deposit_transaction.bridge_from_address == "0xa62693542764185c01ea0e34f96ece0fa32dcbf7"
    assert deposit_transaction.bridge_to_address == "0xa62693542764185c01ea0e34f96ece0fa32dcbf7"

    assert deposit_transaction.amount == 270000000000000000

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.BRIDGE_ETH.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_deposit_erc20_by_unofficial_remote_call():
    # Ethereum Mainnet 20274498, 286, 0xcfb1285ddbd40f3930ef5fbb348ba44c6653fc0dee98a9685d608164bb0217d4
    # https://etherscan.io/tx/0xcfb1285ddbd40f3930ef5fbb348ba44c6653fc0dee98a9685d608164bb0217d4https://etherscan.io/tx/0xcfb1285ddbd40f3930ef5fbb348ba44c6653fc0dee98a9685d608164bb0217d4
    # https://optimistic.etherscan.io/tx/0xb2659fbfa927282a8cc92c4be9d6eb531b98edc788daad459636fafcf371720e
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0xcfb1285ddbd40f3930ef5fbb348ba44c6653fc0dee98a9685d608164bb0217d4",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0xbeb5fc579115071764c7423a4f12edde41f106ed")

    assert deposit_transactions is not None

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0x33acafa67b8b57634a598c717c88b11adc918da4a08b64a476811ca06f0d6498"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 123748
    assert deposit_transaction.block_number == 20274498
    assert deposit_transaction.block_timestamp == 1720595219
    assert deposit_transaction.block_hash == "0x7980549a5051934062a133d2ed239771f0b8183265e895a6c3b59a9955166e63"
    assert deposit_transaction.transaction_hash == "0xcfb1285ddbd40f3930ef5fbb348ba44c6653fc0dee98a9685d608164bb0217d4"
    assert deposit_transaction.from_address == "0x360537542135943e8fc1562199aea6d0017f104b"
    assert deposit_transaction.to_address == "0x39ea01a0298c315d149a490e34b59dbf2ec7e48f"
    assert deposit_transaction.local_token_address is None
    assert deposit_transaction.remote_token_address is None

    assert (
        deposit_transaction.l2_transaction_hash == "0xb2659fbfa927282a8cc92c4be9d6eb531b98edc788daad459636fafcf371720e"
    )

    assert deposit_transaction.bridge_from_address == "0x360537542135943e8fc1562199aea6d0017f104b"
    assert deposit_transaction.bridge_to_address == "0x39ea01a0298c315d149a490e34b59dbf2ec7e48f"

    assert deposit_transaction.amount == 0

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.NORMAL_CROSS_CHAIN_CALL.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_deposit_erc20():
    # Ethereum Mainnet 20274853, 63, 0xa2b668b6c15ee6864b1942944c0bc238016c3e5c450298836b4a3c4674123346
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0xa2b668b6c15ee6864b1942944c0bc238016c3e5c450298836b4a3c4674123346",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0xbeb5fc579115071764c7423a4f12edde41f106ed")

    assert deposit_transactions is not None

    assert len(deposit_transactions) == 1

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0x1427e048631d0bbe068caea49ebd47f507f6669dbd828c70d51431cc40d4d07e"
    assert deposit_transaction.version == 1
    assert deposit_transaction.index == 123763
    assert deposit_transaction.block_number == 20274853
    assert deposit_transaction.block_timestamp == 1720599491
    assert deposit_transaction.block_hash == "0x1ddfa6bbb61bd35592b00ca6c2b9ffa9d8c8f8bb529833ed10ff6a766b112c89"
    assert deposit_transaction.transaction_hash == "0xa2b668b6c15ee6864b1942944c0bc238016c3e5c450298836b4a3c4674123346"
    assert deposit_transaction.from_address == "0x0a6c69327d517568e6308f1e1cd2fd2b2b3cd4bf"
    assert deposit_transaction.to_address == "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"
    assert deposit_transaction.local_token_address == "0xc3248a1bd9d72fa3da6e6ba701e58cbf818354eb"
    assert deposit_transaction.remote_token_address == "0x5052fa4a2a147eaaa4c0242e9cc54a10a4f42070"

    assert deposit_transaction.bridge_from_address == "0x0a6c69327d517568e6308f1e1cd2fd2b2b3cd4bf"
    assert deposit_transaction.bridge_to_address == "0x0a6c69327d517568e6308f1e1cd2fd2b2b3cd4bf"

    assert deposit_transaction.amount == 50244875614794891263

    assert (
        deposit_transaction.l2_transaction_hash == "0x9e1febd944595313cf4162640ed929d0dc3634c94ff468f5761bfaa2e181b942"
    )

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.BRIDGE_ERC20.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_cyber_native_deposit_eth():
    # Ethereum Mainnet 20274054, 381, 0x8c2db781f5dc5428e64818199450e3542ac1c5fb5540ffe9fbb3feccecb229fb
    # https://etherscan.io/tx/0x8c2db781f5dc5428e64818199450e3542ac1c5fb5540ffe9fbb3feccecb229fb
    # https://cyber.socialscan.io/tx/0xb073ce67822d9166435b830b6bad9da25bc7e7b01adb5273e4af6856be70caa7
    transaction = get_transaction_from_rpc(
        DEFAULT_ETHEREUM_RPC,
        "0x8c2db781f5dc5428e64818199450e3542ac1c5fb5540ffe9fbb3feccecb229fb",
    )

    deposit_transactions = parse_transaction_deposited_event(transaction, "0x1d59bc9fce6b8e2b1bf86d4777289ffd83d24c99")

    assert deposit_transactions is not None

    assert len(deposit_transactions) == 1

    deposit_transaction = deposit_transactions[0]

    assert deposit_transaction.msg_hash == "0xb073ce67822d9166435b830b6bad9da25bc7e7b01adb5273e4af6856be70caa7"
    assert deposit_transaction.version == None
    assert deposit_transaction.index == None
    assert deposit_transaction.block_number == 20274054
    assert deposit_transaction.block_timestamp == 1720589867
    assert deposit_transaction.block_hash == "0xb0c82b792d3dbe552e08adba9a9332ac454fb183f3773fe99faaa00766bc43d3"
    assert deposit_transaction.transaction_hash == "0x8c2db781f5dc5428e64818199450e3542ac1c5fb5540ffe9fbb3feccecb229fb"
    assert deposit_transaction.from_address == "0x6363b69296b61264c18b880420614d0f89ffd064"
    assert deposit_transaction.to_address == "0x1d59bc9fce6b8e2b1bf86d4777289ffd83d24c99"
    assert deposit_transaction.local_token_address is None
    assert deposit_transaction.remote_token_address is None

    assert deposit_transaction.bridge_from_address == "0x6363b69296b61264c18b880420614d0f89ffd064"
    assert deposit_transaction.bridge_to_address == "0x6363b69296b61264c18b880420614d0f89ffd064"

    assert deposit_transaction.amount == 1000000000000000

    assert (
        deposit_transaction.l2_transaction_hash == "0xb073ce67822d9166435b830b6bad9da25bc7e7b01adb5273e4af6856be70caa7"
    )

    assert deposit_transaction.bridge_transaction_type == BedRockFunctionCallType.NATIVE_BRIDGE_ETH.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_withdrawal_remote_call():
    # Optimism 122581675, 31, 0xc92762c6f9031d15fe3073dda117f9254372f677b31f14d7a477d0cb9133ac60
    transaction = get_transaction_from_rpc(
        DEFAULT_OPTIMISM_RPC,
        "0xc92762c6f9031d15fe3073dda117f9254372f677b31f14d7a477d0cb9133ac60",
    )

    withdrawal_transactions = parse_message_passed_event(transaction, "0x4200000000000000000000000000000000000016")

    assert withdrawal_transactions is not None

    assert len(withdrawal_transactions) == 1

    withdrawal_transaction = withdrawal_transactions[0]

    assert (
        withdrawal_transaction.withdrawal_hash == "0x3645fe754a8f8049b41a452b789be3f99c215a3a09657a8670391b429d71f8e6"
    )
    assert withdrawal_transaction.version == 1
    assert withdrawal_transaction.index == 18701

    assert withdrawal_transaction.block_number == 122581675
    assert withdrawal_transaction.block_timestamp == 1720762127
    assert withdrawal_transaction.block_hash == "0xf0fcec03a97ca7d25a0b139b203a4f9e2f7a6f9f581928530bb04954ea529b4c"
    assert (
        withdrawal_transaction.transaction_hash == "0xc92762c6f9031d15fe3073dda117f9254372f677b31f14d7a477d0cb9133ac60"
    )
    assert withdrawal_transaction.from_address == "0x2cad75e380ddb12329231df6793a0343917be8b3"
    assert withdrawal_transaction.to_address == "0xf9d64d54d32ee2bdceaabfa60c4c438e224427d0"

    assert withdrawal_transaction.local_token_address is None
    assert withdrawal_transaction.remote_token_address is None

    assert withdrawal_transaction.bridge_from_address == "0x2cad75e380ddb12329231df6793a0343917be8b3"
    assert withdrawal_transaction.bridge_to_address == "0xf9d64d54d32ee2bdceaabfa60c4c438e224427d0"

    assert withdrawal_transaction.amount == 0

    assert withdrawal_transaction.sender == "0x432006ced3bba818e3d0d8730426b32bb34a42ab"
    assert withdrawal_transaction.target == "0x5c2149869146dea55cdd1cf2dd828e4e1548bb2a"
    assert withdrawal_transaction.gas_limit == 850000
    assert withdrawal_transaction.value == 0

    assert withdrawal_transaction.bridge_transaction_type == BedRockFunctionCallType.NORMAL_CROSS_CHAIN_CALL.value


@pytest.mark.indexer
@pytest.mark.indexer_bridge
def test_bridge_optimism_withdrawal_erc20():
    # Optimism 122241892, 62, 0xcccd460201549a2269c13f15b92a84212f1b27b79cf8f9b54af282ac25356a0d

    transaction = get_transaction_from_rpc(
        DEFAULT_OPTIMISM_RPC,
        "0xcccd460201549a2269c13f15b92a84212f1b27b79cf8f9b54af282ac25356a0d",
    )

    withdrawal_transactions = parse_message_passed_event(transaction, "0x4200000000000000000000000000000000000016")

    assert withdrawal_transactions is not None

    assert len(withdrawal_transactions) == 1

    withdrawal_transaction = withdrawal_transactions[0]

    assert (
        withdrawal_transaction.withdrawal_hash == "0xf88586fbf9f45c5bcd49c81a4120fb59619e83dc7249af42a0d75d12db53e5fe"
    )
    assert withdrawal_transaction.version == 1
    assert withdrawal_transaction.index == 18491

    assert withdrawal_transaction.block_number == 122241892
    assert withdrawal_transaction.block_timestamp == 1720082561
    assert withdrawal_transaction.block_hash == "0x3fca2935b68347c83e0f46bf1a8dbf19111a453ceb97754b1fe69ce3c32834c4"
    assert (
        withdrawal_transaction.transaction_hash == "0xcccd460201549a2269c13f15b92a84212f1b27b79cf8f9b54af282ac25356a0d"
    )
    assert withdrawal_transaction.from_address == "0x404f1f962aac5d40f9f8ed924cca74ec3c1bb48a"
    assert withdrawal_transaction.to_address == "0x4200000000000000000000000000000000000010"

    assert withdrawal_transaction.local_token_address == "0x2ebd53d035150f328bd754d6dc66b99b0edb89aa"
    assert withdrawal_transaction.remote_token_address == "0x9a2e53158e12bc09270af10c16a466cb2b5d7836"

    assert withdrawal_transaction.bridge_from_address == "0x404f1f962aac5d40f9f8ed924cca74ec3c1bb48a"
    assert withdrawal_transaction.bridge_to_address == "0x404f1f962aac5d40f9f8ed924cca74ec3c1bb48a"

    assert withdrawal_transaction.amount == 9737750000000000000000

    assert withdrawal_transaction.sender == "0x4200000000000000000000000000000000000010"
    assert withdrawal_transaction.target == "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"
    assert withdrawal_transaction.gas_limit == 200000
    assert withdrawal_transaction.value == 0

    assert withdrawal_transaction.bridge_transaction_type == BedRockFunctionCallType.BRIDGE_ERC20.value


# TODO ADD MORE TESTS
# - More chain
# - Proven Finalized
# - State Batch
