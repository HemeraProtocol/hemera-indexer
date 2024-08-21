import pytest

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.domain.block import Block
from indexer.exporters.console_item_exporter import ConsoleItemExporter
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

    job_scheduler.clear_data_buff()
