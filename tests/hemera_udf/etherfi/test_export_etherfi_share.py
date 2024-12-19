import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.etherfi.domains import EtherFiPositionValuesD, EtherFiShareBalanceCurrentD, EtherFiShareBalanceD
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_exporter
@pytest.mark.serial
def test_export_etherfi_share_job():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "export_ether_fi_share_job": {
                "liquidity_pool_address": "0x308861A430be4cce5502d0A12724771Fc6DaF216",
                "eeth_address": "0x35fa164735182de50811e8e2e824cfb9b6118ac2",
            }
        },
        required_output_types=[EtherFiShareBalanceD, EtherFiPositionValuesD, EtherFiShareBalanceCurrentD],
    )

    job_scheduler.run_jobs(
        start_block=21120813,
        end_block=21120848,
    )

    data_buff = job_scheduler.get_data_buff()

    token_balances = data_buff[EtherFiShareBalanceD.type()]
    assert len(token_balances) == 13

    current_token_balances = data_buff[EtherFiShareBalanceCurrentD.type()]
    assert len(current_token_balances) == 9

    positions = data_buff[EtherFiPositionValuesD.type()]
    assert len(positions) == 3
