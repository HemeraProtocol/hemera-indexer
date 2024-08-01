import pytest

from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.modules.user_ops.domain.user_operations import UserOperationsResult
from indexer.tests import CYBER_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_jobs
@pytest.mark.indexer_jobs_user_ops
def test_export_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=None,
        required_output_types=[UserOperationsResult],
    )

    job_scheduler.run_jobs(
        start_block=2423182,
        end_block=2424182,
    )
    assert len(job_scheduler.get_data_buff().get(UserOperationsResult.type())) > 0
    job_scheduler.clear_data_buff()
