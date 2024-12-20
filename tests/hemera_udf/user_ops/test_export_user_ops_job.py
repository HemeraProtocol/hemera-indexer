import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.user_ops.domains import UserOperationsResult
from tests_commons import CYBER_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_jobs
@pytest.mark.indexer_jobs_user_ops
def test_export_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[UserOperationsResult],
    )

    job_scheduler.run_jobs(
        start_block=2423182,
        end_block=2424182,
    )
    assert len(job_scheduler.get_data_buff().get(UserOperationsResult.type())) > 0
    job_scheduler.clear_data_buff()
