import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.meme_agent.domains.clanker import ClankerCreatedTokenD
from hemera_udf.meme_agent.domains.larry import LarryCreatedTokenD
from hemera_udf.meme_agent.domains.virtuals import VirtualsCreatedTokenD
from tests_commons import BASE_PUBLIC_NODE_RPC_URL

config = {
    "export_meme_token_created_job": {
        "clanker_factory_address_v0": "0x250c9FB2b411B48273f69879007803790A6AeA47",
        "clanker_factory_address_v1": "0x9b84fce5dcd9a38d2d01d5d72373f6b6b067c3e1",
        "virtuals_factory_address_v0": "0x41a0f5b16b10748d594b471850bd7488f929beba",
        "virtuals_factory_address_v1": "0x94Bf9622348Cf5598D9A491Fa809194Cf85A0D61",
        "larry_factory_address": [
            "0x5faAb5D52790916ed9c2C159960006151e311bA0",
            "0xb3a720f17902b7d2e8c38c5044c3b20e8ac9c27c",
        ],
    }
}


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_lanker_v1_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=config,
        required_output_types=[ClankerCreatedTokenD],
    )

    job_scheduler.run_jobs(
        start_block=23603785,
        end_block=23603786,
    )

    data_buff = job_scheduler.get_data_buff()

    token = data_buff[ClankerCreatedTokenD.type()]
    assert len(token) == 1


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_virtuals_v1_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=config,
        required_output_types=[VirtualsCreatedTokenD],
    )

    job_scheduler.run_jobs(
        start_block=23268136,
        end_block=23268137,
    )

    data_buff = job_scheduler.get_data_buff()

    token = data_buff[VirtualsCreatedTokenD.type()]
    assert len(token) == 1


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_larry_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(BASE_PUBLIC_NODE_RPC_URL, batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config=config,
        required_output_types=[LarryCreatedTokenD],
    )

    job_scheduler.run_jobs(
        start_block=23526723,
        end_block=23526723,
    )

    data_buff = job_scheduler.get_data_buff()

    token = data_buff[LarryCreatedTokenD.type()]
    assert len(token) == 1
