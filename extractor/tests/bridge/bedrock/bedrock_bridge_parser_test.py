import pytest

from extractor.bridge.bedrock.bedrock_bridge_parser import parse_transaction_deposited_event
from extractor.tests.json_rpc_to_dataclass import get_transaction_from_rpc
from extractor.types import Log


@pytest.mark.bridge
def test_bridge_manta_pacific_transaction_deposited_eth():

    # Ethereum Mainnet 20273058, 188, 0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243
    # https://manta.socialscan.io/tx/0xe579c588d55fea0b4fcf50058fba654b5ef9f7770c79d946e8e673d18a550cd7#eventlog
    # https://etherscan.io/tx/0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243
    transaction = get_transaction_from_rpc(
        "https://ethereum-rpc.publicnode.com", "0x849321b3fafc4c1a51239cd8cfbe5f832dfa8f7a364bd551f2dc99b66d095243"
    )
    deposit_transaction = parse_transaction_deposited_event(transaction, "0x9168765ee952de7c6f8fc6fad5ec209b960b7622")
    assert deposit_transaction is not None
