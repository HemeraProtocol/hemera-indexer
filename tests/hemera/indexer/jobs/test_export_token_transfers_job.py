import pytest

from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from tests_commons import ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, ETHEREUM_PUBLIC_NODE_RPC_URL, LINEA_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(LINEA_PUBLIC_NODE_RPC_URL, batch=True)
        ),
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
