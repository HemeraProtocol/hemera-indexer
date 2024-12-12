#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 11:29
# @Author  will
# @File  test_arb_eth.py
# @Brief
from dataclasses import asdict

import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.bridge.arbitrum.arb_parser import (
    ArbitrumStateBatchConfirmed,
    ArbitrumStateBatchCreated,
    ArbitrumTransactionBatch,
)
from hemera_udf.bridge.domains.arbitrum import (
    ArbitrumL1ToL2TransactionOnL1,
    ArbitrumL1ToL2TransactionOnL2,
    ArbitrumL2ToL1TransactionOnL1,
    ArbitrumL2ToL1TransactionOnL2,
)
from tests_commons import ARBITRUM_PUBLIC_NODE_RPC_URL, ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_l1_to_l2_deposit_eth_on_l1():
    """
    l1_tnx_hash = '0x496e1f86b07b0db956e68f026f74286e829605249e7714db6d1f9ae40b27d941'
    """
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "contract_list": [
                "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
                "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f",
            ],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL1],
    )

    job_scheduler.run_jobs(
        start_block=20316414,
        end_block=20316414,
    )

    data_buff = job_scheduler.get_data_buff()
    send = data_buff[ArbitrumL1ToL2TransactionOnL1.type()][0]
    send = asdict(send)
    assert send is not None
    assert send["msg_hash"] == "0xf448aff385bf01d8815d14f01fe5eba92f43631bacb83c467089139c1defe0f4"
    assert send["index"] == 1612917
    assert send["l1_block_number"] == 20316414
    assert send["l1_transaction_hash"] == "0x496e1f86b07b0db956e68f026f74286e829605249e7714db6d1f9ae40b27d941"
    assert send["l1_token_address"] is None
    assert send["amount"] == 604110835137788

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_l2_to_l1_deposit_eth_on_l2():
    """
    l2_tnx_hash = '0xf448aff385bf01d8815d14f01fe5eba92f43631bacb83c467089139c1defe0f4'
    """
    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "contract_list": ["0x000000000000000000000000000000000000006e"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL2],
    )

    job_scheduler.run_jobs(
        start_block=232679023,
        end_block=232679023,
    )

    data_buff = job_scheduler.get_data_buff()
    confirm = data_buff[ArbitrumL1ToL2TransactionOnL2.type()][0]
    confirm = asdict(confirm)
    assert confirm is not None
    assert confirm["msg_hash"] == "0xf448aff385bf01d8815d14f01fe5eba92f43631bacb83c467089139c1defe0f4"
    assert confirm["l2_block_number"] == 232679023

    job_scheduler.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_l1_to_l2_deposit_erc20():
    """
    l1_tnx_hash = '0xfbb5c06259e7e5d86a43a0b1fad25622ed7fd0fe483f8ab2cf547f994725c12c'
    l2_tnx_hash = '0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b'
    """
    eth_job = JobScheduler(
        item_exporters=[ConsoleItemExporter()],
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        config={
            "contract_list": [
                "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
                "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f",
                "0x72Ce9c846789fdB6fC1f34aC4AD25Dd9ef7031ef",
            ],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        batch_size=10,
        max_workers=1,
        required_output_types=[ArbitrumL1ToL2TransactionOnL1],
    )
    eth_job.run_jobs(
        start_block=20317463,
        end_block=20317463,
    )
    send = eth_job.get_data_buff()[ArbitrumL1ToL2TransactionOnL1.type()][0]
    send = asdict(send)
    assert send is not None
    assert send["msg_hash"] == "0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b"
    assert send["index"] == 1613082
    assert send["l1_block_number"] == 20317463
    assert send["l1_transaction_hash"] == "0xfbb5c06259e7e5d86a43a0b1fad25622ed7fd0fe483f8ab2cf547f994725c12c"
    assert send["l1_token_address"] == "0x43d4a3cd90ddd2f8f4f693170c9c8098163502ad"
    assert send["amount"] == 57851710337182203872875

    eth_job.clear_data_buff()

    arb_job = JobScheduler(
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)),
        item_exporters=[ConsoleItemExporter()],
        batch_size=10,
        max_workers=1,
        config={
            "contract_list": ["0x000000000000000000000000000000000000006e"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL2],
    )
    arb_job.run_jobs(
        start_block=232729523,
        end_block=232729523,
    )
    confirm = arb_job.get_data_buff()[ArbitrumL1ToL2TransactionOnL2.type()][0]
    confirm = asdict(confirm)
    assert confirm is not None
    assert confirm["msg_hash"] == "0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b"
    assert confirm["l2_block_number"] == 232729523

    arb_job.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_l2_to_l1_withdraw():
    """
    l2_tnx_hash = '0xe08b22ab1e5849bd19a1d3f4a63abf3d7757e8af21b975f4202d3c5896fad7fd'
    l1_tnx_hash = '0x1013dea84e83985fa2dd7dbf4ff71dced8c98d1e442e47f0ec39ac5fe4b2008a'
    """
    arb_job = JobScheduler(
        item_exporters=[ConsoleItemExporter()],
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ARBITRUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        config={
            "contract_list": ["0x0000000000000000000000000000000000000064"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        batch_size=10,
        max_workers=1,
        required_output_types=[ArbitrumL2ToL1TransactionOnL2],
    )
    arb_job.run_jobs(
        start_block=213672440,
        end_block=213672440,
    )

    send = arb_job.get_data_buff()[ArbitrumL2ToL1TransactionOnL2.type()][0]
    assert send is not None
    send = asdict(send)
    assert send["msg_hash"] == 119208
    assert send["index"] == 119208
    assert send["l2_block_number"] == 213672440
    assert send["l2_transaction_hash"] == "0xe08b22ab1e5849bd19a1d3f4a63abf3d7757e8af21b975f4202d3c5896fad7fd"
    assert send["amount"] == 234577589862530059
    assert send["l2_token_address"] == "0xfae103dc9cf190ed75350761e95403b7b8afa6c0"

    arb_job.clear_data_buff()

    eth_job = JobScheduler(
        item_exporters=[ConsoleItemExporter()],
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        config={
            "contract_list": ["0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        batch_size=10,
        max_workers=1,
        required_output_types=[ArbitrumL2ToL1TransactionOnL1],
    )
    eth_job.run_jobs(
        start_block=19975906,
        end_block=19975906,
    )

    confirm = eth_job.get_data_buff()[ArbitrumL2ToL1TransactionOnL1.type()][0]
    assert confirm is not None
    confirm = asdict(confirm)
    assert confirm["msg_hash"] == 119208
    assert confirm["l1_block_number"] == 19975906
    assert confirm["l1_transaction_hash"] == "0x1013dea84e83985fa2dd7dbf4ff71dced8c98d1e442e47f0ec39ac5fe4b2008a"

    eth_job.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_state_batch_eth():
    # node_created_tnx_hash = '0x3772f60c09379b147a80086f185b9fc3b7151a871fb48fa674e40ffa970b4aa4'

    eth_job = JobScheduler(
        item_exporters=[ConsoleItemExporter()],
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        config={
            "contract_list": ["0x5eF0D09d1E6204141B4d37530808eD19f60FBa35"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        batch_size=10,
        max_workers=1,
        required_output_types=[ArbitrumStateBatchCreated],
    )
    eth_job.run_jobs(
        start_block=20275296,
        end_block=20275296,
    )

    txn_create = eth_job.get_data_buff()[ArbitrumStateBatchCreated.type()][0]
    txn_create = asdict(txn_create)
    assert txn_create is not None
    assert txn_create["node_num"] == 15406
    assert txn_create["create_l1_block_number"] == 20275296
    assert txn_create["parent_node_hash"] == "0x119838a50b7f9c34ba3314e1150903045bd9562bf261ae5ccf77b913f9fedb74"
    assert txn_create["node_hash"] == "0x032624aca1628fd9ffc5206258c2d56562c5c7055482ffba40c757f9409abb5e"
    eth_job.clear_data_buff()

    eth_job_1 = JobScheduler(
        item_exporters=[ConsoleItemExporter()],
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL, batch=True)
        ),
        config={
            "contract_list": ["0x5eF0D09d1E6204141B4d37530808eD19f60FBa35"],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        batch_size=10,
        max_workers=1,
        required_output_types=[ArbitrumStateBatchConfirmed],
    )
    eth_job_1.run_jobs(
        start_block=20275326,
        end_block=20275326,
    )

    txn_confirm = eth_job_1.get_data_buff()[ArbitrumStateBatchConfirmed.type()][0]
    txn_confirm = asdict(txn_confirm)
    assert txn_confirm is not None
    assert txn_confirm["node_num"] == 15253
    assert txn_confirm["block_hash"] == "0x3483d1e5a7d0e9625b3ee0df6455ec084b6f37cda8aac0f4543766a506b5eefa"
    assert txn_confirm["send_root"] == "0x63d44891a7f8aaafe29a97e05c59f8058fb9881c9115e01532963dacd0cf0a89"
    assert txn_confirm["l1_block_number"] == 20275326
    assert txn_confirm["l1_transaction_hash"] == "0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d"

    eth_job_1.clear_data_buff()


@pytest.mark.indexer
@pytest.mark.indexer_bridge
@pytest.mark.indexer_bridge_arbitrum
@pytest.mark.serial
def test_transaction_batch_eth():
    # 0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82
    eth_job = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={
            "contract_list": [
                "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
                "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f",
                "0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6",
            ],
            "l2_chain_id": 42161,
            "transaction_batch_offset": 22207816,
        },
        required_output_types=[ArbitrumTransactionBatch],
    )

    eth_job.run_jobs(
        start_block=20274992,
        end_block=20274992,
    )

    txn_batch = eth_job.get_data_buff()[ArbitrumTransactionBatch.type()][0]
    txn_batch = asdict(txn_batch)
    assert txn_batch["batch_index"] == 643250
    assert txn_batch["l1_block_number"] == 20274992
    assert txn_batch["l1_block_timestamp"] == 1720601171
    assert txn_batch["l1_block_hash"] == "0x97541c0bb58e4e71bdeec02001149e5a9a9e90a29b14e81464be9e89a46bce22"
    assert txn_batch["l1_transaction_hash"] == "0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82"
    assert txn_batch["start_block_number"] == 230683543
    assert txn_batch["end_block_number"] == 230683798

    eth_job.clear_data_buff()
