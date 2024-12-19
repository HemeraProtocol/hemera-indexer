import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from tests_commons import LINEA_PUBLIC_NODE_RPC_URL, MANTLE_PUBLIC_NODE_DEBUG_RPC_URL, MANTLE_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_current_token_balance_job():
    # ERC1155 current token balance case
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(MANTLE_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(MANTLE_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[TokenBalance, CurrentTokenBalance],
    )

    job_scheduler.run_jobs(
        start_block=68891458,
        end_block=68891458,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[TokenBalance.type()]
    assert len(token_balances) == 33

    current_token_balances = data_buff[CurrentTokenBalance.type()]
    assert len(current_token_balances) == 33


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_current_token_balance_job_mul():
    # ERC1155 current token balance case
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(MANTLE_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(MANTLE_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[TokenBalance, CurrentTokenBalance],
        multicall=True,
    )

    job_scheduler.run_jobs(
        start_block=68891458,
        end_block=68891458,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[TokenBalance.type()]
    assert len(token_balances) == 33

    current_token_balances = data_buff[CurrentTokenBalance.type()]
    assert len(current_token_balances) == 33


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_balance_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[TokenBalance],
    )

    job_scheduler.run_jobs(
        start_block=2786950,
        end_block=2786951,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[TokenBalance.type()]
    assert len(token_balances) == 38

    assert (
        TokenBalance(
            address="0x0bb407287c5e2bde71371e8daf2a2c0acdfdefb1",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x1c0246a02637c4dbbf8e05f3d4fb9423efed8ea4",
            token_id=None,
            token_type="ERC20",
            token_address="0x4af15ec2a0bd43db75dd04e62faa3b8ef36b00d5",
            balance=3412651394117526832,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x2933749e45796d50eba9a352d29eed6fe58af8bb",
            token_id=None,
            token_type="ERC20",
            token_address="0x4af15ec2a0bd43db75dd04e62faa3b8ef36b00d5",
            balance=11300410000000000000,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x3a742bf78f96def72b1f1eac6342cf56135f1d9b",
            token_id=9,
            token_type="ERC1155",
            token_address="0x34be5b8c30ee4fde069dc878989686abe9884470",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x45cc15d7c85d2250365614e9644ade9ced31fa42",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=143200,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x4a7f90c5a4e9d82f659845b63a867a841b5077e0",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x032b241de86a8660f1ae0691a4760b426ea246d7",
            token_id=None,
            token_type="ERC20",
            token_address="0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x5520989bf88eb2c1f07e4045a7e005b14fac59f9",
            token_id=None,
            token_type="ERC20",
            token_address="0x7a61fd2092a3933831e826c08f0d12913fefb96c",
            balance=10000000000,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x564e52bbdf3adf10272f3f33b00d65b2ee48afff",
            token_id=None,
            token_type="ERC20",
            token_address="0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f",
            balance=25526472243269302972,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x564e52bbdf3adf10272f3f33b00d65b2ee48afff",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=764672545771,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x64a027738ae95b55143f9f9ea090e26ba8ac380b",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x69efe7b830ddc778fb6324170640785407f0739a",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x745755f79a355534c849a00a5b0174c7254e7bf6",
            token_id=None,
            token_type="ERC721",
            token_address="0xc0b4ab5cb0fdd6f5dfddb2f7c10c4c6013f97bf2",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x8731d54e9d02c286767d56ac03e8037c07e01e98",
            token_id=None,
            token_type="ERC20",
            token_address="0x224d8fd7ab6ad4c6eb4611ce56ef35dec2277f03",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x95c83da0424086bb73fbbef021dce9928b9a8d42",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x9f54b7c5e586c7f5ba51a4aea6c04dc07f452fb1",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xa822ceb9a24bb573c6778b62a5ffcf89a47cfdb7",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xaad094f6a75a14417d39f04e690fc216f080a41a",
            token_id=None,
            token_type="ERC20",
            token_address="0x224d8fd7ab6ad4c6eb4611ce56ef35dec2277f03",
            balance=773453172028894508994,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xb9a8b15726a87374b5815298903b62c51124d2ef",
            token_id=113247277653770418760022260810496049574803889485188683378163371717968523979889,
            token_type="ERC1155",
            token_address="0x967035b7cc9a323c6019fb0b9c53a308d2ca551c",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xba291e9baf96865903ac9a15f3d79e626763faee",
            token_id=None,
            token_type="ERC20",
            token_address="0xc5cb997016c9a3ac91cbe306e59b048a812c056f",
            balance=1320,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc37544014a0a8d4a1531330e6bd37341e35a102e",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc446dad99f88fca40dc63f362abf5dc9c288697e",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc8ed0d5ecd221a60d785992ac5a605c7f9878d2f",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xf4687413290779a2d5be4f31833aad8f8092ee06",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xf4cac65ba0fea020b2b962c54dc5da81ca66dbae",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x0ffade29e94fd7d87e9824b99e4802d53947c0b1",
            token_id=None,
            token_type="ERC721",
            token_address="0xb18b7847072117ae863f71f9473d555d601eb537",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x41ee6f16d92ae3281506a0b8ce4b856d8ab5feb7",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x477ff8a0e799b39d3172888f994bee64b901648e",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x6be4a44775be622a1c7e16535fae615e17448893",
            token_id=None,
            token_type="ERC721",
            token_address="0x26ee4ba1f0017f411c400a729115c4389e85c42c",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x6f6b19991706e0ff9b00f2840c5453b5080a89e3",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x7160570bb153edd0ea1775ec2b2ac9b65f1ab61b",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=2690357899599,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x87e963a4ddf8c6a67d7137815b3e39f7ccf8de3b",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x91dbd6013523e1ee97084e9a5dca34fdb2019fbf",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xae20b98bc62c3be64bca9d9d5cf6d4f47f733d57",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xbc7594e91849ffd6ddf2004b9df39e211a903408",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc6241c622eb4b4a8ab32aef11b0ce6ee45fd5673",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xebb3af678b24d187dc17fd3b4beb2b3fbd426fd4",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=0,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xeffaef1626c95428834937577bcdce064e20edee",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_balance_job_mul():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[TokenBalance],
        multicall=True,
    )

    job_scheduler.run_jobs(
        start_block=2786950,
        end_block=2786951,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[TokenBalance.type()]
    assert len(token_balances) == 38

    assert (
        TokenBalance(
            address="0x0bb407287c5e2bde71371e8daf2a2c0acdfdefb1",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x1c0246a02637c4dbbf8e05f3d4fb9423efed8ea4",
            token_id=None,
            token_type="ERC20",
            token_address="0x4af15ec2a0bd43db75dd04e62faa3b8ef36b00d5",
            balance=3412651394117526832,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x2933749e45796d50eba9a352d29eed6fe58af8bb",
            token_id=None,
            token_type="ERC20",
            token_address="0x4af15ec2a0bd43db75dd04e62faa3b8ef36b00d5",
            balance=11300410000000000000,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x3a742bf78f96def72b1f1eac6342cf56135f1d9b",
            token_id=9,
            token_type="ERC1155",
            token_address="0x34be5b8c30ee4fde069dc878989686abe9884470",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x45cc15d7c85d2250365614e9644ade9ced31fa42",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=143200,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x4a7f90c5a4e9d82f659845b63a867a841b5077e0",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x032b241de86a8660f1ae0691a4760b426ea246d7",
            token_id=None,
            token_type="ERC20",
            token_address="0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x5520989bf88eb2c1f07e4045a7e005b14fac59f9",
            token_id=None,
            token_type="ERC20",
            token_address="0x7a61fd2092a3933831e826c08f0d12913fefb96c",
            balance=10000000000,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x564e52bbdf3adf10272f3f33b00d65b2ee48afff",
            token_id=None,
            token_type="ERC20",
            token_address="0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f",
            balance=25526472243269302972,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x564e52bbdf3adf10272f3f33b00d65b2ee48afff",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=764672545771,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x64a027738ae95b55143f9f9ea090e26ba8ac380b",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x69efe7b830ddc778fb6324170640785407f0739a",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x745755f79a355534c849a00a5b0174c7254e7bf6",
            token_id=None,
            token_type="ERC721",
            token_address="0xc0b4ab5cb0fdd6f5dfddb2f7c10c4c6013f97bf2",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x8731d54e9d02c286767d56ac03e8037c07e01e98",
            token_id=None,
            token_type="ERC20",
            token_address="0x224d8fd7ab6ad4c6eb4611ce56ef35dec2277f03",
            balance=0,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x95c83da0424086bb73fbbef021dce9928b9a8d42",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x9f54b7c5e586c7f5ba51a4aea6c04dc07f452fb1",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xa822ceb9a24bb573c6778b62a5ffcf89a47cfdb7",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xaad094f6a75a14417d39f04e690fc216f080a41a",
            token_id=None,
            token_type="ERC20",
            token_address="0x224d8fd7ab6ad4c6eb4611ce56ef35dec2277f03",
            balance=773453172028894508994,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xb9a8b15726a87374b5815298903b62c51124d2ef",
            token_id=113247277653770418760022260810496049574803889485188683378163371717968523979889,
            token_type="ERC1155",
            token_address="0x967035b7cc9a323c6019fb0b9c53a308d2ca551c",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xba291e9baf96865903ac9a15f3d79e626763faee",
            token_id=None,
            token_type="ERC20",
            token_address="0xc5cb997016c9a3ac91cbe306e59b048a812c056f",
            balance=1320,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc37544014a0a8d4a1531330e6bd37341e35a102e",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc446dad99f88fca40dc63f362abf5dc9c288697e",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc8ed0d5ecd221a60d785992ac5a605c7f9878d2f",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xf4687413290779a2d5be4f31833aad8f8092ee06",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xf4cac65ba0fea020b2b962c54dc5da81ca66dbae",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786950,
            block_timestamp=1710005722,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x0ffade29e94fd7d87e9824b99e4802d53947c0b1",
            token_id=None,
            token_type="ERC721",
            token_address="0xb18b7847072117ae863f71f9473d555d601eb537",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x41ee6f16d92ae3281506a0b8ce4b856d8ab5feb7",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x477ff8a0e799b39d3172888f994bee64b901648e",
            token_id=None,
            token_type="ERC721",
            token_address="0x66ccc220543b6832f93c2082edd7be19c21df6c0",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x6be4a44775be622a1c7e16535fae615e17448893",
            token_id=None,
            token_type="ERC721",
            token_address="0x26ee4ba1f0017f411c400a729115c4389e85c42c",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x6f6b19991706e0ff9b00f2840c5453b5080a89e3",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x7160570bb153edd0ea1775ec2b2ac9b65f1ab61b",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=2690357899599,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x87e963a4ddf8c6a67d7137815b3e39f7ccf8de3b",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0x91dbd6013523e1ee97084e9a5dca34fdb2019fbf",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xae20b98bc62c3be64bca9d9d5cf6d4f47f733d57",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xbc7594e91849ffd6ddf2004b9df39e211a903408",
            token_id=None,
            token_type="ERC721",
            token_address="0xc043bce9af87004398181a8de46b26e63b29bf99",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xc6241c622eb4b4a8ab32aef11b0ce6ee45fd5673",
            token_id=None,
            token_type="ERC721",
            token_address="0x510581cefd1a4c651aa6727957f283c665647485",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xebb3af678b24d187dc17fd3b4beb2b3fbd426fd4",
            token_id=None,
            token_type="ERC20",
            token_address="0x176211869ca2b568f2a7d4ee941e073a821ee1ff",
            balance=0,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )
    assert (
        TokenBalance(
            address="0xeffaef1626c95428834937577bcdce064e20edee",
            token_id=None,
            token_type="ERC721",
            token_address="0x780de722234532f7d61ca3d147574f44a85c4244",
            balance=1,
            block_number=2786951,
            block_timestamp=1710005726,
        )
        in token_balances
    )

    job_scheduler.clear_data_buff()
