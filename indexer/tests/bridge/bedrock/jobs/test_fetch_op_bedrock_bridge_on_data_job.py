import pytest

from enumeration.entity_type import EntityType
from indexer.domain.transaction import Transaction
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.modules.bridge.domain.op_bedrock import OpL1ToL2DepositedTransaction
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.util
def test_fetch_op_bedrock_bridge_on_data():

    job_scheduler = JobScheduler(
        entity_types=EntityType.BRIDGE,
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)),
        item_exporter=ConsoleItemExporter(),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "optimism_portal_proxy": "0x9168765ee952de7c6f8fc6fad5ec209b960b7622"
        },
        required_output_types=[OpL1ToL2DepositedTransaction]
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273060,
    )

    data_buff = job_scheduler.get_data_buff()
    print(data_buff[Transaction.type()])