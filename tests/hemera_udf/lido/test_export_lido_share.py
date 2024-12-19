import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.lido.domains import LidoPositionValuesD, LidoShareBalanceCurrentD, LidoShareBalanceD
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_lido_share_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={"export_lido_share_job": {"seth_address": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84"}},
        required_output_types=[LidoShareBalanceD, LidoShareBalanceCurrentD, LidoPositionValuesD],
    )

    job_scheduler.run_jobs(
        start_block=21120813,
        end_block=21120848,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[LidoShareBalanceD.type()]
    assert len(token_balances) == 11

    current_token_balances = data_buff[LidoShareBalanceCurrentD.type()]
    assert len(current_token_balances) == 10

    positions = data_buff[LidoPositionValuesD.type()]
    assert len(positions) == 1
