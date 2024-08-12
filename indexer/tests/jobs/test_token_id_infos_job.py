import pytest

from indexer.domain.token_id_infos import *
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.tests import CYBER_PUBLIC_NODE_RPC_URL
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_token_id_info_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(
                CYBER_PUBLIC_NODE_RPC_URL,
                batch=True,
            )
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[
            ERC721TokenIdChange,
            ERC721TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC1155TokenIdDetail,
        ],
    )

    job_scheduler.run_jobs(
        start_block=4536864,
        end_block=4536864,
    )

    job_scheduler.clear_data_buff()
