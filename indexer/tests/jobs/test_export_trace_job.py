import pytest

from enumeration.entity_type import EntityType
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.tests import ETHEREUM_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.export_job
def test_export_job():
    job_scheduler = JobScheduler(
        entity_types=EntityType.TOKEN_TRANSFER,
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://eth-mainnet.g.alchemy.com/v2/W1Ea7v4VM47L97TiMscNOt-eLxIHpdou", batch=True)),
        item_exporter=ConsoleItemExporter(),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=None,
        required_output_types=[ContractInternalTransaction]
    )

    job_scheduler.run_jobs(
        start_block=20273057,
        end_block=20273058,
    )
