#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 11:29
# @Author  will
# @File  test_fetch_arb_bridge_on_data_job.py
# @Brief
import pytest

from extractor.bridge.items import L1_TO_L2_DEPOSITED_TRANSACTION_ON_L1, L2_TO_L1_WITHDRAWN_TRANSACTION_PROVEN, \
    L2_TO_L1_WITHDRAWN_TRANSACTION_FINALIZED, ARB_TRANSACTION_BATCH, ARB_STATE_BATCH
from extractor.jobs.fetch_filter_data_job import FetchFilterDataJob
from utils.provider import get_provider_from_uri
from utils.thread_local_proxy import ThreadLocalProxy
from extractor.bridge.arbitrum.arbitrum_bridge_parser import ArbitrumL1BridgeDataExtractor, ArbitrumL2BridgeDataExtractor

"""
DODO 
op-l1 {
  bridgeOnChain = "L1"
  contractAddresses = [
	"0xc0856971702b02a5576219540bd92dae79a79288", "0xd62ef8d8c71d190417c6ce71f65795696c069f09", "0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d", "0xaeb5fe2f7003881c3a8ebae9664e8607f3935d53", "0xbb94635f882f03f7641b742f5e3070e6b5108b71", "0xe3661c8313b35ba310ad89e113561f3c983dc761"
  ]
}

op-l2 {
  bridgeOnChain = "L2"
  contractAddresses = [
  "0x000000000000000000000000000000000000006e", "0x0000000000000000000000000000000000000064", "0xbb94635f882f03f7641b742f5e3070e6b5108b71"
  ]
}

op-batch {
  bridgeOnChain = "BATCH"
  contractAddresses = [
	"0xc475f82504ca2aaec3c966bddb19a5c738f22c46", "0x297c7b1bbe30353de62936b6722894fca2d1010e", "0x67ad6c79e33ea9e523e0e68961456d0ac7a973cc", "0xaeb5fe2f7003881c3a8ebae9664e8607f3935d53", "0xbc4cc964ef0ea5792a398f9e738edf368a34f003"
  ]

"""

@pytest.mark.util
def test_l1_to_l2_deposit_eth():
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


@pytest.mark.util
def test_l2_to_l1_withdraw():
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


@pytest.mark.util
def test_state_batch():
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


@pytest.mark.util
def test_transaction_batch():
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_TRANSACTION_BATCH],
        start_block=20311480,
        end_block=20311480,
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
