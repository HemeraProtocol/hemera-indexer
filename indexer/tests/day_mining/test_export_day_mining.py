import pytest

from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordTraitsActiveness
from indexer.tests import CYBER_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_jobs
@pytest.mark.indexer_jobs_day_mining
def test_export_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(CYBER_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=10,
        max_workers=5,
        config={},
        required_output_types=[AllFeatureValueRecordTraitsActiveness],
    )

    job_scheduler.run_jobs(
        start_block=1,
        end_block=100,
    )
    assert len(job_scheduler.get_data_buff().get(AllFeatureValueRecordTraitsActiveness.type())) > 0
    job_scheduler.clear_data_buff()
