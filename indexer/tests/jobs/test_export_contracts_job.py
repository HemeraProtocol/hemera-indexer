import pytest

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.contract import Contract
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.tests import LINEA_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_coin_balance_job():
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
        required_output_types=[Contract],
    )

    job_scheduler.run_jobs(
        start_block=2786950,
        end_block=2786951,
    )

    data_buff = job_scheduler.get_data_buff()

    assert len(data_buff.keys()) == 7
    assert len(data_buff["block"]) == 2

    assert "trace" in data_buff
    assert len(data_buff["trace"]) == 250
    trace = data_buff["trace"][93]
    assert trace.transaction_hash == '0x66b22e745dcbe0fb06a6d865755464897db9f05f1557af481b709525b4f04197'
    assert trace.trace_id == '2786950_14_14'
    assert trace.input == '0x27258b22912214269b9b891a0d7451974030ba13207d3bf78e515351609de9dd8a339686'
    assert trace.trace_address == [1, 0, 3, 0]

    assert "contract_internal_transaction" in data_buff
    assert len(data_buff["contract_internal_transaction"]) == 68
    contract_inter_trx = data_buff["contract_internal_transaction"][58]
    assert contract_inter_trx.transaction_hash == '0x986675201b0016f5098e4a94291e01fbe732776caaf8ef5eef2b07e593eeb5de'
    assert contract_inter_trx.trace_id == '2786951_25_1'
    assert contract_inter_trx.input == '0xfb89f3b1'
    assert contract_inter_trx.trace_address == [0]

    assert "update_block_internal_count" in data_buff
    assert len(data_buff["update_block_internal_count"]) == 2
    update_block = data_buff["update_block_internal_count"][1]
    assert update_block.hash == '0x4948e6fd5d8f181fe14b147609710f9cc6af9819d803f4604a71ffebc9a39164'
    assert update_block.number == 2786951
    assert update_block.internal_transactions_count == 0
    assert update_block.traces_count == 97

    assert "contract" in data_buff
    assert len(data_buff["contract"]) == 1
    contract = data_buff["contract"][0]
    assert contract.block_number == 2786950
    assert contract.block_hash == '0x6a823afb4e04e5193f5217f773124a41bee7b02864266015494f5dea6ec6679c'
    assert contract.contract_creator == '0xc44827c51d00381ed4c52646aeab45b455d200eb'

    job_scheduler.clear_data_buff()
