import os
from enum import Enum

GAS_LIMIT: int = int(os.environ.get("GAS_LIMIT", 50_000_000))


class Network(Enum):
    Mainnet = (1, 14353601)
    Ropsten = (3, 0)
    Rinkeby = (4, 0)
    Gorli = (5, 0)
    Optimism = (10, 4286263)
    CostonTestnet = (16, 0)
    ThundercoreTestnet = (18, 0)
    SongbirdCanaryNetwork = (19, 0)
    Cronos = (25, 0)
    RSK = (30, 0)
    RSKTestnet = (31, 0)
    Kovan = (42, 0)
    Bsc = (56, 0)
    OKC = (66, 0)
    OptimismKovan = (69, 0)
    BscTestnet = (97, 0)
    Gnosis = (100, 0)
    Velas = (106, 0)
    Thundercore = (108, 0)
    Coston2Testnet = (114, 0)
    Fuse = (122, 0)
    Heco = (128, 0)
    Polygon = (137, 25770160)
    Fantom = (250, 0)
    Boba = (288, 0)
    KCC = (321, 0)
    ZkSync = (324, 0)
    OptimismGorli = (420, 0)
    Astar = (592, 0)
    Metis = (1088, 0)
    Moonbeam = (1284, 0)
    Moonriver = (1285, 0)
    MoonbaseAlphaTestnet = (1287, 0)
    Milkomeda = (2001, 0)
    Kava = (2222, 0)
    FantomTestnet = (4002, 0)
    Canto = (7700, 0)
    Klaytn = (8217, 0)
    Base = (8453, 5022)
    EvmosTestnet = (9000, 0)
    Evmos = (9001, 0)
    Holesky = (17000, 77)
    Arbitrum = (42161, 7654707)
    Celo = (42220, 0)
    Oasis = (42262, 0)
    AvalancheFuji = (43113, 0)
    Avax = (43114, 0)
    GodwokenTestnet = (71401, 0)
    Godwoken = (71402, 0)
    Mumbai = (80001, 0)
    ArbitrumRinkeby = (421611, 0)
    ArbitrumGorli = (421613, 0)
    Sepolia = (11155111, 0)
    Aurora = (1313161554, 0)
    Harmony = (1666600000, 0)
    PulseChain = (369, 0)
    PulseChainTestnet = (943, 0)
    MANTLE = (5000, 304717)

    def __init__(self, value, deploy_block_number=0):
        self._value = value
        self._deploy_block_number = deploy_block_number

    @property
    def value(self):
        return self._value

    @property
    def deploy_block_number(self):
        return self._deploy_block_number

    @classmethod
    def from_value(cls, value):
        for network in cls:
            if network.value == value:
                return network
        raise ValueError(f"Invalid network value: {value}")


MULTICALL3_ADDRESSES = {
    Network.Mainnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Ropsten: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Rinkeby: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Gorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Optimism: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.CostonTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ThundercoreTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.SongbirdCanaryNetwork: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Cronos: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.RSK: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.RSKTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Kovan: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Bsc: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.OKC: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.OptimismKovan: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.BscTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Gnosis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Velas: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Thundercore: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Coston2Testnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Fuse: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Heco: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Polygon: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Fantom: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Boba: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.KCC: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ZkSync: "0x47898B2C52C957663aE9AB46922dCec150a2272c",
    Network.OptimismGorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Astar: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Metis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Moonbeam: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Moonriver: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.MoonbaseAlphaTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Milkomeda: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.FantomTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Canto: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Klaytn: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.EvmosTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Evmos: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Arbitrum: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Celo: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Oasis: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.AvalancheFuji: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Avax: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.GodwokenTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Godwoken: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Mumbai: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ArbitrumRinkeby: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.ArbitrumGorli: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Sepolia: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Aurora: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Harmony: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.PulseChain: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.PulseChainTestnet: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Base: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.Holesky: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Network.MANTLE: "0xcA11bde05977b3631167028862bE2a173976CA11",
}
