import pytest

from enumeration.entity_type import EntityType
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.export_job
def test_export_transaction_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=None,
        required_output_types=[Log]
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273058,
    )
