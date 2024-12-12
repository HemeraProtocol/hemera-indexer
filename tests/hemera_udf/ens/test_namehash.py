#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 15:14
# @Author  will
# @File  test_namehash.py
# @Brief
from dataclasses import asdict

import pytest

from hemera.indexer.controller.scheduler.job_scheduler import JobScheduler
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.exporters.console_item_exporter import ConsoleItemExporter
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy
from hemera_udf.hemera_ens.ens_handler import EnsConfLoader, EnsHandler
from hemera_udf.hemera_ens.ens_hash import compute_node_label, get_label, namehash
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL


@pytest.mark.indexer
@pytest.mark.ens
@pytest.mark.serial
def test_namehash():
    demo_name = "maxga23.eth"
    demo_node = "0xb13b15972f7f65be1ed1313293e4f5e5a006c5420cec802d35dc7e88e7bab183"
    demo_label = "0x1914fcc93afc2b367d581bbae8d17a775b5852b620c32608dd2bdf5d99e89ab5"
    demo_base_node = "93cdeb708b7545dc668eb9280176169d1c33cfd8ed6f04690a0bcc88a93fc4ae"

    name_hash = namehash(demo_name)
    assert name_hash == demo_node
    label = get_label(demo_name.split(".")[0])
    assert label == demo_label
    res = compute_node_label(demo_base_node, demo_label)
    assert res == demo_node
    print("ok!")
    print(get_label("adion"))
    print(get_label("vitalik\x00"))


@pytest.mark.indexer
@pytest.mark.ens
@pytest.mark.serial
def test_mirgate_names():

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(ETHEREUM_PUBLIC_NODE_RPC_URL, batch=True)
        ),
        item_exporters=[ConsoleItemExporter()],
        batch_size=100,
        debug_batch_size=1,
        max_workers=5,
        config={},
        required_output_types=[Transaction, Log],
    )

    job_scheduler.run_jobs(
        start_block=9412121,
        end_block=9412121,
    )
    ens_handler = EnsHandler(EnsConfLoader(ETHEREUM_PUBLIC_NODE_RPC_URL))

    df = job_scheduler.get_data_buff()
    for tnx in df["transaction"]:
        if tnx.hash == "0x4967988122e8160400f1ed7acd315310aac98c42b2f5d1de3064fcb44a16ecc3":
            break
    logs = []
    for log in df["log"]:
        if log.transaction_hash == tnx.hash:
            logs.append(asdict(log))

    res = ens_handler.process(asdict(tnx), logs)
    for rr in res:
        assert rr.node is not None
