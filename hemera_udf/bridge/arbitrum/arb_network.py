#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/7/15 16:39
# @Author  will
# @File  arb_network.py
# @Brief
from enum import Enum


class Network(Enum):
    Mainnet = 1
    Ropsten = 3
    Rinkeby = 4
    Gorli = 5
    Optimism = 10
    CostonTestnet = 16
    ThundercoreTestnet = 18
    SongbirdCanaryNetwork = 19
    Cronos = 25
    RSK = 30
    RSKTestnet = 31
    Kovan = 42
    Bsc = 56
    OKC = 66
    OptimismKovan = 69
    BscTestnet = 97
    Gnosis = 100
    Velas = 106
    Thundercore = 108
    Coston2Testnet = 114
    Fuse = 122
    Heco = 128
    Polygon = 137
    Fantom = 250
    Boba = 288
    KCC = 321
    ZkSync = 324
    OptimismGorli = 420
    Astar = 592
    Metis = 1088
    Moonbeam = 1284
    Moonriver = 1285
    MoonbaseAlphaTestnet = 1287
    Milkomeda = 2001
    Kava = 2222
    FantomTestnet = 4002
    Canto = 7700
    Klaytn = 8217
    Base = 8453
    EvmosTestnet = 9000
    Evmos = 9001
    Holesky = 17000
    Arbitrum = 42161
    Celo = 42220
    Oasis = 42262
    AvalancheFuji = 43113
    Avax = 43114
    GodwokenTestnet = 71401
    Godwoken = 71402
    Mumbai = 80001
    ArbitrumRinkeby = 421611
    ArbitrumGorli = 421613
    Sepolia = 11155111
    Aurora = 1313161554
    Harmony = 1666600000
    PulseChain = 369
    PulseChainTestnet = 943
    MANTLE = 5000
    DODO_TESTNET = 53457

    @classmethod
    def from_value(cls, value):
        for network in cls:
            if network.value == value:
                return network
        raise ValueError(f"Invalid network value: {value}")
