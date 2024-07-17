#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 11:29
# @Author  will
# @File  test_arb_eth.py
# @Brief
import pytest
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy

from models.bridge.arbitrum.arb_parser import ArbitrumTransactionBatch, ArbitrumStateBatchCreated, \
    ArbitrumStateBatchConfirmed
from models.bridge.arbitrum.arbitrum_bridge_parser import ArbitrumL1BridgeDataExtractor, \
    ArbitrumL2BridgeDataExtractor
from models.bridge.items import ARB_L1ToL2_ON_L1, ARB_L2ToL1_ON_L2, ARB_L2ToL1_ON_L1
from models.jobs.fetch_filter_data_job import FetchFilterDataJob

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

l1_rpc = "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
l2_rpc = "https://dodochain-testnet.alt.technology"

@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_dodo():
    """
    l1_tnx_hash = '0x2a26e82e2720c5c0592b686aba6832f2ee26009af80a0c149f00ad79ee11139e'
    l2_tnx_hash = '0x74e8ac4359905ad27ee403bc13d976640d9febf4e663009cd0a41134a103516a'
    "https://dodochain-testnet.alt.technology"
    "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
    """
    l1_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L1ToL2_ON_L1],
        export_keys=[ARB_L1ToL2_ON_L1],
        start_block=37277407,
        end_block=37277407,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(contract_list=['0xd62ef8d8c71d190417c6ce71f65795696c069f09', '0xc0856971702b02a5576219540bd92dae79a79288', '0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d'])
    )
    l1_job.run()
    send_lis = l1_job._data_buff[ARB_L1ToL2_ON_L1]
    assert len(send_lis) == 9
    # all kinds
    # kind 3
    k3 = send_lis[2]
    assert k3['index'] == 2
    assert k3['l1_block_number'] == 37277407
    assert k3['from_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    assert k3['to_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    # TODO confirm what l2hash should be
    # assert k3['msg_hash'] == ''

    # kind 11
    k11 = send_lis[0]
    assert k11['index'] == 0
    assert k11['l1_block_number'] == 37277407
    assert k11['from_address'] == '0x0000000000000000000000000000000000000000'
    # TODO confirm what l2hash should be
    # assert k11['msg_hash'] == ''
    # kind9
    k9 = send_lis[1]
    assert k9['index'] == 1
    assert k9['l1_block_number'] == 37277407
    assert k9['from_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    assert k9['to_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    # TODO confirm what l2hash should be
    # assert k9['msg_hash'] == ''

    l2_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L2],
        export_keys=[ARB_L2ToL1_ON_L2],
        start_block=232679023,
        end_block=232679023,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL2BridgeDataExtractor(contract_list=['0x000000000000000000000000000000000000006e'])
    )
    l2_job.run()
    confirm = l2_job._data_buff[ARB_L2ToL1_ON_L2][0]
    assert confirm is not None
    assert confirm['msg_hash'] == '0xf448aff385bf01d8815d14f01fe5eba92f43631bacb83c467089139c1defe0f4'
    assert confirm['l2_block_number'] == 232679023


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_usdc():
    # 46298492
    l1_tnx_hash = '0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0'
    #
    l2_tnx_hash = '0x74e8ac4359905ad27ee403bc13d976640d9febf4e663009cd0a41134a103516a'



@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_gld():
    pass


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_erc20():
    """
    l1_tnx_hash = '0xfbb5c06259e7e5d86a43a0b1fad25622ed7fd0fe483f8ab2cf547f994725c12c'
    l2_tnx_hash = '0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b'
    """
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L1ToL2_ON_L1],
        export_keys=[ARB_L1ToL2_ON_L1],
        start_block=20317463,
        end_block=20317463,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://ethereum-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(contract_list=['0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a', '0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f', '0x72Ce9c846789fdB6fC1f34aC4AD25Dd9ef7031ef'])
    )
    eth_job.run()
    send = eth_job._data_buff[ARB_L1ToL2_ON_L1][0]
    assert send is not None
    assert send['msg_hash'] == '0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b'
    assert send['index'] == 1613082
    assert send['l1_block_number'] == 20317463
    assert send['l1_transaction_hash'] == '0xfbb5c06259e7e5d86a43a0b1fad25622ed7fd0fe483f8ab2cf547f994725c12c'
    assert send['l1_token_address'] == '0x43d4a3cd90ddd2f8f4f693170c9c8098163502ad'
    assert send['amount'] == 57851710337182203872875

    arb_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L2],
        start_block=232729523,
        end_block=232729523,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL2BridgeDataExtractor(contract_list=['0x000000000000000000000000000000000000006e'])
    )
    arb_job.run()
    confirm = arb_job._data_buff[ARB_L2ToL1_ON_L2][0]
    assert confirm is not None
    assert confirm['msg_hash'] == '0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b'
    assert confirm['l2_block_number'] == 232729523


@pytest.mark.test_arb_eth
def test_l2_to_l1_withdraw():
    """
    l2_tnx_hash = '0xe08b22ab1e5849bd19a1d3f4a63abf3d7757e8af21b975f4202d3c5896fad7fd'
    l1_tnx_hash = '0x1013dea84e83985fa2dd7dbf4ff71dced8c98d1e442e47f0ec39ac5fe4b2008a'
    """
    arb_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L2],
        export_keys=[ARB_L2ToL1_ON_L2],
        start_block=213672440,
        end_block=213672440,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri("https://arbitrum-one-rpc.publicnode.com", batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL2BridgeDataExtractor(contract_list=['0x0000000000000000000000000000000000000064'])
    )
    arb_job.run()
    send = arb_job._data_buff[ARB_L2ToL1_ON_L2][0]
    assert send is not None
    assert send['msg_hash'] == 119208
    assert send['index'] == 119208
    assert send['l2_block_number'] == 213672440
    assert send['l2_transaction_hash'] == '0xe08b22ab1e5849bd19a1d3f4a63abf3d7757e8af21b975f4202d3c5896fad7fd'
    assert send['amount'] == 234577589862530059
    assert send['l2_token_address'] == '0xfae103dc9cf190ed75350761e95403b7b8afa6c0'

    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L1],
        export_keys=[ARB_L2ToL1_ON_L1],
        start_block=19975906,
        end_block=19975906,
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
    confirm = eth_job._data_buff[ARB_L2ToL1_ON_L1][0]
    assert confirm is not None
    assert confirm['msg_hash'] == 119208
    assert confirm['l1_block_number'] == 19975906
    assert confirm['l1_transaction_hash'] == '0x1013dea84e83985fa2dd7dbf4ff71dced8c98d1e442e47f0ec39ac5fe4b2008a'


@pytest.mark.test_arb_eth
def test_state_batch_eth():
    # node_created_tnx_hash = '0x3772f60c09379b147a80086f185b9fc3b7151a871fb48fa674e40ffa970b4aa4'
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumStateBatchCreated.type()],
        export_keys=[ArbitrumStateBatchCreated.type()],
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
    txn_create = eth_job._data_buff[ArbitrumStateBatchCreated.type()][0]
    assert txn_create is not None
    assert txn_create['node_num'] == 15406
    assert txn_create['create_l1_block_number'] == 20275296
    assert txn_create['parent_node_hash'] == '0x119838a50b7f9c34ba3314e1150903045bd9562bf261ae5ccf77b913f9fedb74'
    assert txn_create['node_hash'] == '0x032624aca1628fd9ffc5206258c2d56562c5c7055482ffba40c757f9409abb5e'

    # node_confirmed_tnx_hash = '0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d'
    eth_job1 = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumStateBatchConfirmed.type()],
        export_keys=[ArbitrumStateBatchConfirmed.type()],
        start_block=20275326,
        end_block=20275326,
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
    txn_confirm = eth_job1._data_buff[ArbitrumStateBatchConfirmed.type()][0]
    assert txn_confirm is not None
    assert txn_confirm['node_num'] == 15253
    assert txn_confirm['block_hash'] == '0x3483d1e5a7d0e9625b3ee0df6455ec084b6f37cda8aac0f4543766a506b5eefa'
    assert txn_confirm['send_root'] == '0x63d44891a7f8aaafe29a97e05c59f8058fb9881c9115e01532963dacd0cf0a89'
    assert txn_confirm['l1_block_number'] == 20275326
    assert txn_confirm['l1_transaction_hash'] == '0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d'


@pytest.mark.test_arb_eth
def test_transaction_batch_eth():
    # 0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumTransactionBatch.type()],
        export_keys=[ArbitrumTransactionBatch.type()],
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
    txn_batch = data_buf['arbitrum_transaction_batch'][0]
    assert txn_batch['batch_index'] == 643250
    assert txn_batch['l1_block_number'] == 20274992
    assert txn_batch['l1_block_timestamp'] == 1720601171
    assert txn_batch['l1_block_hash'] == '0x97541c0bb58e4e71bdeec02001149e5a9a9e90a29b14e81464be9e89a46bce22'
    assert txn_batch['l1_transaction_hash'] == '0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82'
    assert txn_batch['start_block_number'] == 230683544
    assert txn_batch['end_block_number'] == 230683798
