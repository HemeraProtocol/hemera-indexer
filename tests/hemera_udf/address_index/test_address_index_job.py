import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.address_index.domains import *
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_address_index
@pytest.mark.serial
def test_export_address_index_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[
            TokenAddressNftInventory,
            AddressTransaction,
            AddressTokenTransfer,
            AddressNftTransfer,
            AddressTokenHolder,
        ],
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273058,
    )

    job_scheduler.clear_data_buff()
