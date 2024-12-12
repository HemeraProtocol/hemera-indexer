import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.bridge.domains.op_bedrock import OpL1ToL2DepositedTransaction
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_optimism
def test_fetch_op_bedrock_bridge_on_data():

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={"optimism_portal_proxy": "0x9168765ee952de7c6f8fc6fad5ec209b960b7622"},
        required_output_types=[OpL1ToL2DepositedTransaction],
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273060,
    )

    data_buff = job_scheduler.get_data_buff()

    job_scheduler.clear_data_buff()
