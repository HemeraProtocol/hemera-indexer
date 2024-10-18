import pytest

from common.utils.web3_utils import ZERO_ADDRESS
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.tests import ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, ETHEREUM_PUBLIC_NODE_RPC_URL, LINEA_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_job():
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
        required_output_types=[ERC721TokenTransfer, ERC1155TokenTransfer],
    )

    job_scheduler.run_jobs(
        start_block=7510938,
        end_block=7510938,
    )

    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.keys()) == 10

    assert "token" in data_buff.keys()
    assert len(data_buff["token"]) == 7
    token = data_buff["token"][2]
    assert token.address == "0xc5cb997016c9a3ac91cbe306e59b048a812c056f"
    assert token.decimals == 0
    assert token.total_supply == 4641010509

    assert "update_token" in data_buff.keys()
    assert len(data_buff["update_token"]) == 4
    update_token = data_buff["update_token"][1]
    update_token.address = "0x176211869ca2b568f2a7d4ee941e073a821ee1ff"
    update_token.total_supply = 28705661218277

    assert "erc20_token_transfer" in data_buff.keys()
    assert len(data_buff["erc20_token_transfer"]) == 9
    erc20_token_transfer = data_buff["erc20_token_transfer"][7]
    assert erc20_token_transfer.transaction_hash == "0x4d585ebfdd93037667bdb9ef19a757e6d50d56c33049f17d50304af91ff2df63"
    assert erc20_token_transfer.log_index == 77
    assert erc20_token_transfer.value == 196003266

    assert "erc721_token_transfer" in data_buff.keys()
    assert len(data_buff["erc721_token_transfer"]) == 8
    erc721_token_transfer = data_buff["erc721_token_transfer"][6]
    assert (
        erc721_token_transfer.transaction_hash == "0xd32fb19c93c27d1c55384d3dd2ed87c5cb594e00634c9e5d83ed4540625feb78"
    )
    assert erc721_token_transfer.log_index == 66
    assert erc721_token_transfer.token_id == 4583234

    assert "erc1155_token_transfer" in data_buff.keys()
    assert len(data_buff["erc1155_token_transfer"]) == 3
    erc1155_token_transfer = data_buff["erc1155_token_transfer"][1]
    assert (
        erc1155_token_transfer.transaction_hash == "0x4faa9c58bd864ff7e09a011f9319eba3c12e52f37691ee538ba14f57ef079860"
    )
    assert erc1155_token_transfer.log_index == 35
    assert (
        erc1155_token_transfer.token_id == 50411206725691109941676758658949651974631268551207578819994085010046423484406
    )

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_weth_depoist_transfer_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={"export_tokens_and_transfers_job": {"weth_address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}},
        required_output_types=[ERC20TokenTransfer],
    )

    job_scheduler.run_jobs(
        start_block=20757606,
        end_block=20757606,
    )

    data_buff = job_scheduler.get_data_buff()
    deposit_eth_token_transfers = [
        transfer
        for transfer in data_buff[ERC20TokenTransfer.type()]
        if transfer.block_number == 20757606 and transfer.log_index == 162
    ]
    withdraw_eth_token_transfers = [
        transfer
        for transfer in data_buff[ERC20TokenTransfer.type()]
        if transfer.block_number == 20757606 and transfer.log_index == 167
    ]
    assert len(deposit_eth_token_transfers) == 1
    assert deposit_eth_token_transfers[0].from_address == ZERO_ADDRESS
    assert len(withdraw_eth_token_transfers) == 1
    assert withdraw_eth_token_transfers[0].to_address == ZERO_ADDRESS
    print(withdraw_eth_token_transfers)
    assert len(data_buff[ERC20TokenTransfer.type()]) == 275
    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_weth_depoist_transfer_with_wrong_config_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={"export_tokens_and_transfers_job": {"weth_address": "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111"}},
        required_output_types=[ERC20TokenTransfer],
    )

    job_scheduler.run_jobs(
        start_block=20757606,
        end_block=20757606,
    )

    data_buff = job_scheduler.get_data_buff()
    deposit_eth_token_transfers = [
        transfer
        for transfer in data_buff[ERC20TokenTransfer.type()]
        if transfer.block_number == 20757606 and transfer.log_index == 162
    ]
    withdraw_eth_token_transfers = [
        transfer
        for transfer in data_buff[ERC20TokenTransfer.type()]
        if transfer.block_number == 20757606 and transfer.log_index == 167
    ]
    assert len(deposit_eth_token_transfers) == 0
    assert len(withdraw_eth_token_transfers) == 0
