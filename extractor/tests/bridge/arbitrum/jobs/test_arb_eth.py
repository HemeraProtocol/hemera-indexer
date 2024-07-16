#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 11:29
# @Author  will
# @File  test_arb_eth.py
# @Brief
import pytest

from extractor.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN, \
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED, ARB_TRANSACTION_BATCH, ARB_STATE_BATCH
from extractor.jobs.fetch_filter_data_job import FetchFilterDataJob
from utils.provider import get_provider_from_uri
from utils.thread_local_proxy import ThreadLocalProxy
from extractor.bridge.arbitrum.arbitrum_bridge_parser import ArbitrumL1BridgeDataExtractor, ArbitrumL2BridgeDataExtractor


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_eth():
    """
    l1_tnx_hash = '0xda4bb002306d46ac3d4ec4754f8841e72d82e876231106ecf4eb77f6244de836'
    l2_tnx_hash = '0x358bad7e9e28729b77f41ca3fdd188bcccc5004636d0cf81d7dc2abaed9c84fd'
    """
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1],
        start_block=20310269,
        end_block=20310269,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(contract_list=['0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a', '0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f'])
    )
    eth_job.run()
    arb_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1],
        start_block=232383629,
        end_block=232383629,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(contract_list=['0x000000000000000000000000000000000000006e'])
    )
    arb_job.run()


@pytest.mark.test_arb_eth
def test_l2_to_l1_withdraw():
    """
    l2_tnx_hash = '0xde2d34248ce22eeff376cc4cc8706b5d187cbd6ea585446c3c6d3d94ace5e0af'
    l1_tnx_hash = '0x80620129db9fca3127a072a1898a56dc6bdc8f950ce6b0ff6e7a3057baf7f5fe'
    """
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN],
        start_block=16236515,
        end_block=16236515,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a'])
    )
    eth_job.run()
    arb_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN],
        start_block=45957130,
        end_block=45957130,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(contract_list=['0x0000000000000000000000000000000000000064'])
    )
    arb_job.run()


@pytest.mark.test_arb_eth
def test_state_batch_eth():
    # node_confirmed_tnx_hash = '0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d'
    # node_created_tnx_hash = '0x3772f60c09379b147a80086f185b9fc3b7151a871fb48fa674e40ffa970b4aa4'
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_STATE_BATCH],
        start_block=20275296,
        end_block=20275296,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0x5eF0D09d1E6204141B4d37530808eD19f60FBa35'])
    )
    eth_job.run()
    eth_job1 = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_STATE_BATCH],
        start_block=20311242,
        end_block=20311242,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0x5eF0D09d1E6204141B4d37530808eD19f60FBa35'])
    )
    eth_job1.run()


@pytest.mark.test_arb_eth
def test_transaction_batch_eth():
    # 0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_TRANSACTION_BATCH],
        start_block=20274992,
        end_block=20274992,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://eth.llamarpc.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6'])
    )
    eth_job.run()
    data_buf = eth_job._data_buff
    tnx_batch = data_buf[0]
