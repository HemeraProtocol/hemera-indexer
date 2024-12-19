import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.bridge.domains.morph import (
    MorphDepositedTransactionOnL1,
    MorphDepositedTransactionOnL2,
    MorphWithdrawalTransactionOnL1,
    MorphWithdrawalTransactionOnL2,
)
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL, MORPHL2_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_morph
def test_fetch_morphl2_bridge_on_l1_deposited():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "morph_bridge_on_l1_job": {
                "l1_message_queue_oracle_contract_address": "0x3931ade842f5bb8763164bdd81e5361dce6cc1ef"
            }
        },
        required_output_types=[MorphDepositedTransactionOnL1, MorphWithdrawalTransactionOnL1],
    )

    job_scheduler.run_jobs(
        start_block=21077111,
        end_block=21077112,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphDepositedTransactionOnL1.type())) == 1

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_morph
def test_fetch_morphl2_bridge_on_l1_withdrawal():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "morph_bridge_on_l1_job": {
                "l1_cross_domain_messenger_contract_address": "0xdc71366effa760804dcfc3edf87fa2a6f1623304"
            }
        },
        required_output_types=[MorphDepositedTransactionOnL1, MorphWithdrawalTransactionOnL1],
    )

    job_scheduler.run_jobs(
        start_block=21073775,
        end_block=21073776,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL1.type())) == 1

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_morph
def test_fetch_morphl2_bridge_on_l2_withdrawl():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "morph_bridge_on_l2_job": {
                "l2_cross_domain_messenger_contract_address": "0x5300000000000000000000000000000000000007"
            }
        },
        required_output_types=[MorphDepositedTransactionOnL2, MorphWithdrawalTransactionOnL2],
    )

    job_scheduler.run_jobs(
        start_block=136270,
        end_block=136271,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()

    job_scheduler.run_jobs(
        start_block=96943,
        end_block=96944,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()

    job_scheduler.run_jobs(
        start_block=186757,
        end_block=186758,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_morph
def test_fetch_morphl2_bridge_on_l2_deposited():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "morph_bridge_on_l2_job": {
                "l2_cross_domain_messenger_contract_address": "0x5300000000000000000000000000000000000007"
            }
        },
        required_output_types=[MorphDepositedTransactionOnL2, MorphWithdrawalTransactionOnL2],
    )

    job_scheduler.run_jobs(
        start_block=136270,
        end_block=136271,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()

    job_scheduler.run_jobs(
        start_block=96943,
        end_block=96944,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()

    job_scheduler.run_jobs(
        start_block=186757,
        end_block=186758,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphWithdrawalTransactionOnL2.type())) == 1

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_morph
def test_fetch_morphl2_bridge_on_l2_deposit():
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(MORPHL2_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "morph_bridge_on_l2_job": {
                "l2_cross_domain_messenger_contract_address": "0x5300000000000000000000000000000000000007"
            }
        },
        required_output_types=[MorphDepositedTransactionOnL2, MorphWithdrawalTransactionOnL2],
    )

    job_scheduler.run_jobs(
        start_block=196444,
        end_block=196445,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphDepositedTransactionOnL2.type())) == 2

    job_scheduler.clear_data_buff()

    job_scheduler.run_jobs(
        start_block=196229,
        end_block=196230,
    )
    data_buff = job_scheduler.get_data_buff()
    assert len(data_buff.get(MorphDepositedTransactionOnL2.type())) == 2

    job_scheduler.clear_data_buff()
