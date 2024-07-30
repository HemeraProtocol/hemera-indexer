import pytest

from indexer.domain.token_id_infos import *
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.tests import LINEA_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.export_job
def test_export_token_id_info_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri("https://rpc-tob.mantle.xyz/v1/NTdlM2E1MGM4YTQ5OTg2Yjk0MWYyMWY5", batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://rpc-tob.mantle.xyz/v1/NTdlM2E1MGM4YTQ5OTg2Yjk0MWYyMWY5", batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=None,
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail
        ]
    )

    job_scheduler.run_jobs(
        start_block=
        66887726,
        end_block=
        66887740,
    )
