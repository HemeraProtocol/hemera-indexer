#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/5 10:07
# @Author  will
# @File  test_multicall_helper.py
# @Brief

import pytest
from web3 import Web3

from hemera.common.utils.abi_code_utils import Function
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.indexer.utils.abi_setting import ERC20_BALANCE_OF_FUNCTION
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.abi import AGGREGATE_FUNC, TRY_BLOCK_AND_AGGREGATE_FUNC
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from tests_commons import ETHEREUM_PUBLIC_NODE_RPC_URL

web3 = Web3(Web3.HTTPProvider(ETHEREUM_PUBLIC_NODE_RPC_URL))
multicall_helper = MultiCallHelper(web3, {"batch_size": 100, "multicall": True, "max_workers": 10})


def test_multicall_encode():
    cl1 = Call(
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        function_abi=ERC20_BALANCE_OF_FUNCTION,
        parameters=["0x49866A9CFE9129FbB0B93dCDb4b5eb758Ee3F9Be"],
    )
    cl2 = Call(
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        function_abi=ERC20_BALANCE_OF_FUNCTION,
        parameters=["0xdDE1bb2B8cb427B889567CbDf6527c4E69C0a392"],
    )
    parameters = [[[call.target, hex_str_to_bytes(call.data)] for call in [cl1, cl2]]]
    assert AGGREGATE_FUNC.encode_function_call_data(parameters) == AGGREGATE_FUNC.encode_multicall_data(parameters)

    parameters = [False, [[call.target, hex_str_to_bytes(call.data)] for call in [cl1, cl2]]]
    assert TRY_BLOCK_AND_AGGREGATE_FUNC.encode_function_call_data(
        parameters
    ) == TRY_BLOCK_AND_AGGREGATE_FUNC.encode_multicall_data(parameters)


@pytest.mark.indexer
@pytest.mark.multicall_helper
def test_mutlicall_mantle():
    print("mantle multicall test")
    mweb3 = Web3(Web3.HTTPProvider("https://rpc.mantle.xyz"))
    multicall_helper_mantle = MultiCallHelper(mweb3, {"batch_size": 100, "multicall": True, "max_workers": 10})
    POSITIONS_FUNCTION = Function(
        {
            "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
            "name": "positions",
            "outputs": [
                {"internalType": "uint96", "name": "nonce", "type": "uint96"},
                {"internalType": "address", "name": "operator", "type": "address"},
                {"internalType": "address", "name": "token0", "type": "address"},
                {"internalType": "address", "name": "token1", "type": "address"},
                {"internalType": "uint24", "name": "tickLower", "type": "uint24"},
                {"internalType": "int24", "name": "tickUpper", "type": "int24"},
                {"internalType": "int24", "name": "liquidity", "type": "int24"},
                {"internalType": "uint128", "name": "feeGrowthInside0LastX128", "type": "uint128"},
                {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
                {"internalType": "uint256", "name": "tokensOwed0", "type": "uint256"},
                {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"},
                {"internalType": "uint128", "name": "tokensOwed2", "type": "uint128"},
            ],
            "stateMutability": "view",
            "type": "function",
        }
    )
    target = "0xAAA78E8C4241990B4ce159E105dA08129345946A"
    call = Call(target=target, function_abi=POSITIONS_FUNCTION, parameters=[44296], block_number=70617618)
    multicall_helper_mantle.execute_calls([call])
    assert call.returns is not None


@pytest.mark.indexer
@pytest.mark.multicall_helper
def test_mutlicall_helper():

    usdt = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    dai = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    name_function = Function(
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "name", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    )
    block_number = 2000_0000
    call1 = Call(target=usdt, function_abi=name_function, block_number=block_number)
    call2 = Call(target=usdc, function_abi=name_function, block_number=block_number)
    call3 = Call(target=dai, function_abi=name_function, block_number=block_number)
    multicall_helper.execute_calls([call1, call2, call3])
    assert (call1.returns["name"]) == "Tether USD"
    assert (call2.returns["name"]) == "USD Coin"
    assert (call3.returns["name"]) == "Dai Stablecoin"

    balance_of_function = Function(
        {
            "constant": True,
            "inputs": [{"name": "who", "type": "address"}],
            "name": "balanceOf",
            "outputs": [
                {"name": "who", "type": "uint256"},
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    )
    call = Call(
        target=usdt,
        function_abi=balance_of_function,
        parameters=["0x5041ed759Dd4aFc3a72b8192C143F72f4724081A"],
        block_number=21119829,
    )
    multicall_helper.execute_calls([call])
    assert call.returns["who"] == 301722821308228

    aave_lending_pool = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    fn = Function(
        {
            "inputs": [],
            "name": "getReservesList",
            "outputs": [{"internalType": "address[]", "name": "reserves", "type": "address[]"}],
            "stateMutability": "view",
            "type": "function",
        }
    )
    call = Call(target=aave_lending_pool, function_abi=fn, block_number=21119829)
    multicall_helper.execute_calls([call])
    assert len(call.returns["reserves"]) == 37
    get_user_data = Function(
        {
            "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"internalType": "uint256", "name": "totalCollateralETH", "type": "uint256"},
                {"internalType": "uint256", "name": "totalDebtETH", "type": "uint256"},
                {"internalType": "uint256", "name": "availableBorrowsETH", "type": "uint256"},
                {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                {"internalType": "uint256", "name": "healthFactor", "type": "uint256"},
            ],
            "stateMutability": "view",
            "type": "function",
        }
    )
    call = Call(
        target=aave_lending_pool,
        function_abi=get_user_data,
        parameters=["0x7974b46e7940de2c4d6458c053bdbac0bf111683"],
        block_number=21125855,
    )
    multicall_helper.execute_calls([call])
    assert call.returns["totalCollateralETH"] == 6435876602599020169644
    assert call.returns["totalDebtETH"] == 3129169440974041004676
    assert call.returns["healthFactor"] == 1692899707581926203

    aave_vary_debt_usdc = "0x619beb58998ed2278e08620f97007e1116d5d25b"
    balance_of_function = Function(
        {
            "constant": True,
            "inputs": [{"name": "who", "type": "address"}],
            "name": "balanceOf",
            "outputs": [
                {"name": "who", "type": "uint256"},
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    )
    address = "0x7974b46e7940de2c4d6458c053bdbac0bf111683"
    start_block_number = 15311054
    step = 10000
    times = 100
    calls = []
    for i in range(times):
        calls.append(
            Call(
                target=aave_vary_debt_usdc,
                function_abi=balance_of_function,
                parameters=[address],
                block_number=start_block_number + i * step,
            )
        )
    expected_return = {
        15311054: 1211497204684,
        15321054: 1211583947722,
        15331054: 1211662457976,
        15341054: 1211739596755,
        15351054: 2011863462376,
        15361054: 1521961212765,
        15371054: 1522058377828,
        15381054: 1522146707535,
        15391054: 1522237030571,
        15401054: 1522327385813,
        15411054: 1522420811598,
        15421054: 1522517486328,
        15431054: 1522611769191,
        15441054: 1522698655385,
        15451054: 1522782917133,
        15461054: 1522864737690,
        15471054: 1522948004977,
        15481054: 1523028140079,
        15491054: 1523099540802,
        15501054: 1523169128522,
        15511054: 1523241887199,
        15521054: 1523314215576,
        15531054: 1523382420746,
        15541054: 1523447015748,
        15551054: 1523521065288,
        15561054: 1523599242781,
        15571054: 1523678808795,
        15581054: 1523760678576,
        15591054: 1523841285007,
        15601054: 1523919330667,
        15611054: 1523996532629,
        15621054: 1524077636459,
        15631054: 1524164811480,
        15641054: 1524253205486,
        15651054: 1524344527258,
        15661054: 1524436519632,
        15671054: 1524529216986,
        15681054: 1524626763968,
        15691054: 1524723606823,
        15701054: 1524820164157,
        15711054: 1524916660598,
        15721054: 1525013510507,
        15731054: 1525111618863,
        15741054: 1525211156032,
        15751054: 1525324845924,
        15761054: 1525441049179,
        15771054: 1525559933878,
        15781054: 1525685222563,
        15791054: 1525811689823,
        15801054: 1525936049299,
        15811054: 1526060851688,
        15821054: 1526186052309,
        15831054: 1526305968891,
        15841054: 1526424562668,
        15851054: 1526546546946,
        15861054: 1526670284284,
        15871054: 1526793294324,
        15881054: 1526918264352,
        15891054: 1527046214364,
        15901054: 1527170719583,
        15911054: 1527293001157,
        15921054: 1527415489399,
        15931054: 1527544859705,
        15941054: 771484205282,
        15951054: 771574374183,
        15961054: 771658123238,
        15971054: 771726547737,
        15981054: 871788721854,
        15991054: 871852421261,
        16001054: 871918359896,
        16011054: 871986053346,
        16021054: 872057215243,
        16031054: 872127850551,
        16041054: 872198186402,
        16051054: 872272154205,
        16061054: 872346172060,
        16071054: 872420744951,
        16081054: 872495647971,
        16091054: 872571218213,
        16101054: 872651023072,
        16111054: 872728582706,
        16121054: 872806635141,
        16131054: 872886649964,
        16141054: 872967332407,
        16151054: 873047226902,
        16161054: 873127205611,
        16171054: 873208066729,
        16181054: 873287327059,
        16191054: 873365522185,
        16201054: 873443773806,
        16211054: 873521803586,
        16221054: 873600171293,
        16231054: 873677720772,
        16241054: 973760895360,
        16251054: 973848846639,
        16261054: 973937400170,
        16271054: 974025083151,
        16281054: 974113357204,
        16291054: 974202650650,
        16301054: 974291227149,
    }
    multicall_helper.execute_calls(calls)
    for call in calls:
        assert call.returns["who"] == expected_return[call.block_number]
