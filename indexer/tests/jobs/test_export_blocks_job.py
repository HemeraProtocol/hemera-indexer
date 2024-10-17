import pytest

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.block import Block
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.tests import ETHEREUM_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_job():
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
        required_output_types=[Block],
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273058,
    )

    data_buff = job_scheduler.get_data_buff()

    assert len(data_buff.keys()) == 3

    assert 'block' in data_buff
    assert len(data_buff['block']) == 2
    block = data_buff['block'][0]
    assert block.number == 20273057
    assert block.hash == '0x23466a3906f8be59ce7a0dd0d6ef084f5bcba03386cae49135054fc1d7f03fa0'
    assert block.parent_hash == '0xba166c762e417d338838427251481557f734e53cf5f61cc034d9701c3360b948'
    assert block.extra_data == '0x546974616e2028746974616e6275696c6465722e78797a29'
    assert len(block.transactions) == 167

    assert 'transaction' in data_buff
    assert len(data_buff['transaction']) == 350
    transaction = data_buff['transaction'][183]
    assert transaction.hash == '0xb0f6f719e4f68df5ebc191ee9ddd9d2cf5a03770c58ca042e719b99a22a43bfd'
    assert transaction.input[:10] == '0x9950c080'
    assert transaction.receipt is None

    assert 'block_ts_mapper' in data_buff
    assert len(data_buff['block_ts_mapper']) == 1
    assert data_buff['block_ts_mapper'][0].block_number == 20273057
    assert data_buff['block_ts_mapper'][0].timestamp == 1720576800

    job_scheduler.clear_data_buff()
