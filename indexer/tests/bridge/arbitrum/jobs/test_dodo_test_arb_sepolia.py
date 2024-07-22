#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 11:29
# @Author  will
# @File  test_arb_eth.py
# @Brief
import pytest

from enumeration.entity_type import EntityType
from indexer.jobs.job_scheduler import JobScheduler
from indexer.modules.bridge.domain.arbitrum import ArbitrumL1ToL2TransactionOnL1, ArbitrumL1ToL2TransactionOnL2
from indexer.modules.bridge.items import ARB_L1ToL2_ON_L1
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from dataclasses import dataclass, asdict

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

l1_rpc = ""
#l1_rpc = "https://crimson-magical-uranium.arbitrum-sepolia.quiknode.pro/8e017b6afe915259d38562e178c89a65ec680c39"
l2_rpc = "https://dodochain-testnet.alt.technology"

@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_dodo():
    """
    l1_tnx_hash = '0x2a26e82e2720c5c0592b686aba6832f2ee26009af80a0c149f00ad79ee11139e'
    l2_tnx_hash = '0x74e8ac4359905ad27ee403bc13d976640d9febf4e663009cd0a41134a103516a'
    "https://dodochain-testnet.alt.technology"
    "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"
    """
    l1_job = JobScheduler(
        entity_types=EntityType.BRIDGE,
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(l1_rpc, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)),

        batch_size=10,
        max_workers=1,
        config={
            "contract_list": ['0xd62ef8d8c71d190417c6ce71f65795696c069f09', '0xc0856971702b02a5576219540bd92dae79a79288', '0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d'],
            'l2_chain_id': 53457,
            'transaction_batch_offset': 0
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL1]
    )
    l1_job.run_jobs(
        start_block=37277407,
        end_block=37277407,
    )
    send_lis = l1_job.get_data_buff()[ArbitrumL1ToL2TransactionOnL1.type()]
    l1_job.clear_data_buff()
    assert len(send_lis) == 9
    # all kinds
    # kind 3
    k3 = asdict(send_lis[2])
    assert k3['index'] == 2
    assert k3['l1_block_number'] == 37277407
    assert k3['from_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    assert k3['to_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    # TODO confirm what l2hash should be
    # assert k3['msg_hash'] == 'aa'
    # assert k3['amount'] == 0

    # kind 11
    k11 = asdict(send_lis[0])
    assert k11['index'] == 0
    assert k11['l1_block_number'] == 37277407
    assert k11['from_address'] == '0x0000000000000000000000000000000000000000'
    # TODO confirm what l2hash should be
    # assert k11['msg_hash'] == ''
    # assert k11['amount'] == 101
    # kind9
    k9 = asdict(send_lis[1])
    assert k9['index'] == 1
    assert k9['l1_block_number'] == 37277407
    assert k9['from_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    assert k9['to_address'] == '0xebc4c123515da9525d72d78af5eea9b11e150691'
    # TODO confirm what l2hash should be
    assert k9['msg_hash'] == '0x74e8ac4359905ad27ee403bc13d976640d9febf4e663009cd0a41134a103516a'
    assert k9['amount'] == 0

    l2_job = JobScheduler(
        entity_types=EntityType.BRIDGE,

        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        config={
            "contract_list": ['0x000000000000000000000000000000000000006e'],
            'l2_chain_id': 53457,
            'transaction_batch_offset': 0
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL2]
    )
    l2_job.run_jobs(
        start_block=0,
        end_block=2174,
    )
    confirm = l2_job.get_data_buff()[ArbitrumL1ToL2TransactionOnL2.type()]
    assert confirm is not None
    print([se.msg_hash for se in send_lis])
    print([co.msg_hash for co in confirm])
    # assert confirm['msg_hash'] == '0xf448aff385bf01d8815d14f01fe5eba92f43631bacb83c467089139c1defe0f4'
    # assert confirm['l2_block_number'] == 232679023


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_usdc():
    #
    l1_job = JobScheduler(
        entity_types=EntityType.BRIDGE,

        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        config={
            "contract_list": ['0xd62ef8d8c71d190417c6ce71f65795696c069f09', '0xc0856971702b02a5576219540bd92dae79a79288', '0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d'],
            'l2_chain_id': 53457,
            'transaction_batch_offset': 0
        },
        required_output_types=[ArbitrumL1ToL2TransactionOnL1]
    )
    l1_job.run_jobs(
        start_block=46298492,
        end_block=46298492,
    )
    send_lis = l1_job.get_data_buff()[ArbitrumL1ToL2TransactionOnL1.type()]
    assert len(send_lis) == 1
    send_lis[0] = asdict(send_lis[0])
    assert send_lis[0]['msg_hash'] == '0xcb9ee2ff28bf01623d37596e033f0c77736def463d62bf1bd015bd8bf12b0b3b'
    assert send_lis[0]['l1_block_number'] == 46298492
    assert send_lis[0]['l1_transaction_hash'] == '0x022800446360a100034dc5cbc0563813db6ff4136ca7ff4f777badc2603ac4c0'
    assert send_lis[0]['amount'] == 10000000000000000000
    assert send_lis[0]['l1_token_address'] == '0xd0cf7dfbf09cafab8aef00e0ce19a4638004a364'


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_kind12():
    #
    l1_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L1ToL2_ON_L1],
        export_keys=[ARB_L1ToL2_ON_L1],
        start_block=44594973,
        end_block=44594973,
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
    assert len(send_lis) == 1
    assert send_lis[0]['msg_hash'] == '0x695b1c8f042c71f123379ccce2dea17298d858315d1dedff8704d64b67388eb0'
    assert send_lis[0]['l1_block_number'] == 44594973
    assert send_lis[0]['l1_transaction_hash'] == '0x05bea0b3d43714348f869152769bf3b2f81863339dbd2ce961c2c14f54185d41'
    assert send_lis[0]['amount'] == 100000000000000


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_gld():
    l1_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L1ToL2_ON_L1],
        export_keys=[ARB_L1ToL2_ON_L1],
        start_block=42230445,
        end_block=42230445,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0xd62ef8d8c71d190417c6ce71f65795696c069f09', '0xc0856971702b02a5576219540bd92dae79a79288',
                           '0xa97c7633c747a10dfc8150d3a6dae448a0a6b65d'])
    )
    l1_job.run()
    send_lis = l1_job._data_buff[ARB_L1ToL2_ON_L1]
    assert len(send_lis) == 1
    assert send_lis[0]['msg_hash'] == '0x747f2148ab85ca5e4c6274312cec7258edf0e2ddaa90030581150ac512152000'
    assert send_lis[0]['l1_block_number'] == 42230445
    assert send_lis[0]['l1_transaction_hash'] == '0x1ec81cacb17d39e9521d93f9b22e80590d09a911510fbafa8c48720cfe668ae5'
    assert send_lis[0]['amount'] == 1000000000000000000
    assert send_lis[0]['l1_token_address'] == '0xb5b52dfea4b4bbd665ba9c5e9651449614eec96d'


@pytest.mark.test_arb_eth
def test_l1_to_l2_deposit_erc20():
    """
    l1_tnx_hash = '0xfbb5c06259e7e5d86a43a0b1fad25622ed7fd0fe483f8ab2cf547f994725c12c'
    l2_tnx_hash = '0x7f2e057ff9fe588e822b192636e7dca87982a93666cb5218c8bdae429c283d1b'
    """
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L1ToL2_ON_L1],
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
    l2_tnx_hash = '0x023026939dcbab09a40ca8e83a612bcf280e7fb6f6e4a505b04e2d23b7274648'
    l1_tnx_hash = '0xfea97317e8533d6a0cc3ef49c75a40439793057c3b0f6a414ab3dd57efccb06e'
    """
    arb_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L2],
        export_keys=[ARB_L2ToL1_ON_L2],
        start_block=0,
        end_block=2174,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l2_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL2BridgeDataExtractor(contract_list=['0x0000000000000000000000000000000000000064'])
    )
    arb_job.run()
    send_lis = arb_job._data_buff[ARB_L2ToL1_ON_L2]
    assert send_lis is not None
    assert len(send_lis) == 12
    assert send_lis[0]['msg_hash'] == 0
    assert send_lis[0]['l2_block_number'] == 18
    assert send_lis[0]['amount'] == 100000000000000000

    assert send_lis[11]['msg_hash'] == 11
    assert send_lis[11]['l2_block_number'] == 1915
    assert send_lis[11]['amount'] == 1900000000000000000

    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ARB_L2ToL1_ON_L1],
        export_keys=[ARB_L2ToL1_ON_L1],
        start_block=37326739,
        end_block=37326739,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0xc0856971702b02a5576219540bd92dae79a79288'])
    )
    eth_job.run()
    confirm = eth_job._data_buff[ARB_L2ToL1_ON_L1][0]
    assert confirm is not None
    assert confirm['msg_hash'] == 0
    assert confirm['l1_block_number'] == 37326739
    assert confirm['l1_transaction_hash'] == '0xfea97317e8533d6a0cc3ef49c75a40439793057c3b0f6a414ab3dd57efccb06e'
    assert confirm['value'] == 100000000000000000


@pytest.mark.test_arb_eth
def test_state_batch_eth():
    # node_created_tnx_hash = '0x3772f60c09379b147a80086f185b9fc3b7151a871fb48fa674e40ffa970b4aa4'
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumStateBatchCreated.type()],
        export_keys=[ArbitrumStateBatchCreated.type()],
        start_block=64428750,
        end_block=64428750,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0xbc4cc964ef0ea5792a398f9e738edf368a34f003'])
    )
    eth_job.run()
    txn_create = eth_job._data_buff[ArbitrumStateBatchCreated.type()][0]
    assert txn_create is not None
    assert txn_create['node_num'] == 295
    assert txn_create['create_l1_block_number'] == 64428750
    assert txn_create['parent_node_hash'] == '0x60ac3d3c4bed465ca1554ecc149b811ce5bd793f9de6e9034251c0c53919768c'
    assert txn_create['node_hash'] == '0x2dd9bcdc86b0cc387f7d514ce0a3836537058c89af76f189a3aedf54e2ba5d80'

    # node_confirmed_tnx_hash = '0xec745d2444fa77165db936d1661d69da4234050f715ae5d7b1509200339a8a0d'
    eth_job1 = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumStateBatchConfirmed.type()],
        export_keys=[ArbitrumStateBatchConfirmed.type()],
        start_block=64434169,
        end_block=64434169,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0xbc4cc964ef0ea5792a398f9e738edf368a34f003'])
    )
    eth_job1.run()
    txn_confirm = eth_job1._data_buff[ArbitrumStateBatchConfirmed.type()][0]
    assert txn_confirm is not None
    assert txn_confirm['node_num'] == 295
    assert txn_confirm['block_hash'] == '0x86451c0dfae6b6fa2cd58357c8ba69a42b3786518e8dd33313a462b944790420'
    assert txn_confirm['send_root'] == '0x36c9c2cfae0aaf9e860e68e6cd7659796a576c3a3850ce31c93e9740095d9998'
    assert txn_confirm['l1_block_number'] == 64434169
    assert txn_confirm['l1_transaction_hash'] == '0x3a1ae1cfefa0b5270d612adc783552c8ede8110b95cdb2bea3b6d22064ea865e'


@pytest.mark.test_arb_eth
def test_transaction_batch_eth():
    # 0xfbeaff030508a0ec169d709a24c5f3c07c2a7c595b9647e45e080a54416c7f82
    eth_job = FetchFilterDataJob(
        index_keys=['block', 'transaction', 'receipt', 'log', ArbitrumTransactionBatch.type()],
        export_keys=[ArbitrumTransactionBatch.type()],
        start_block=37291894,
        end_block=37291894,
        t=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=False)
        ),
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(l1_rpc, batch=True)
        ),
        batch_size=10,
        max_workers=1,
        extractor=ArbitrumL1BridgeDataExtractor(
            contract_list=['0x67ad6c79e33ea9e523e0e68961456d0ac7a973cc'])
    )
    eth_job.run()
    data_buf = eth_job._data_buff
    txn_batch = data_buf[ArbitrumTransactionBatch.type()][0]
    assert txn_batch['batch_index'] == 1
    assert txn_batch['l1_block_number'] == 37291894
    assert txn_batch['l1_transaction_hash'] == '0x26128070a1422082afbb4d17bf690c107f4d30b27c1d9d74bd2fdc57f41c3b78'
    assert txn_batch['start_block_number'] == 1
    assert txn_batch['end_block_number'] == 18
