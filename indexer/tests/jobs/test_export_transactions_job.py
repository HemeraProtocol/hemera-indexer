import pytest

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.log import Log
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.tests import ETHEREUM_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_transaction_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[Log],
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273058,
    )

    data_buff = job_scheduler.get_data_buff()

    assert len(data_buff.keys()) == 4
    assert 'block' in data_buff.keys()
    assert 'transaction'in data_buff.keys()
    assert 'log' in data_buff.keys()

    assert len(data_buff['log']) == 827
    log = data_buff['log'][511]
    assert log.transaction_index == 21
    assert log.log_index == 103
    assert log.block_hash == '0x6d5644ab134fe01595e3e0628fe4945a47666f7dba251c2258b99ed7b1705585'
    assert log.transaction_hash == '0xd6e2b0bdb45895c68de4d62f1976c76c7e3583f86244cf17ca1a5d5bf152646e'
    assert log.address == '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
    assert log.topic0 == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    assert log.topic3 is None

    job_scheduler.clear_data_buff()
