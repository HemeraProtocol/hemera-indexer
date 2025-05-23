import os
from dataclasses import dataclass
from typing import ClassVar, Dict

# gas limit for a single call
GAS_LIMIT: int = int(os.environ.get("GAS_LIMIT", 5_000_000))
# for some networks, there may be `MAX_GAS_LIMIT` if this is set, `GAS_LIMIT` will not be used
MAX_GAS_LIMIT: int = int(os.environ.get("MAX_GAS_LIMIT", 0))
# payload limit in KB
RPC_PAYLOAD_SIZE: int = int(os.environ.get("BATCH_SIZE", 250))
# calls limit
CALLS_LIMIT: int = int(os.environ.get("CALLS_LIMIT", 2000))
DEFAULT_MULTICALL_ADDRESS = os.environ.get("DEFAULT_MULTICALL_ADDRESS", "0xcA11bde05977b3631167028862bE2a173976CA11")


@dataclass(frozen=True)
class NetworkConfig:
    chain_id: int
    name: str
    deploy_block_number: int = 2**56
    multicall_address: str = DEFAULT_MULTICALL_ADDRESS

    _networks: ClassVar[Dict[int, "NetworkConfig"]] = {}

    def __post_init__(self):
        NetworkConfig._networks[self.chain_id] = self

    @classmethod
    def from_chain_id(cls, chain_id: int) -> "NetworkConfig":
        if chain_id not in cls._networks:
            raise ValueError(f"Unsupported network chain ID: {chain_id}")
        return cls._networks[chain_id]

    @classmethod
    def get_all_networks(cls) -> Dict[int, "NetworkConfig"]:
        """Get all registered networks."""
        return cls._networks.copy()


MAINNET = NetworkConfig(1, "Mainnet", 14353601)
ROPSTEN = NetworkConfig(3, "Ropsten")
RINKEBY = NetworkConfig(4, "Rinkeby")
GOERLI = NetworkConfig(5, "Goerli")
SEPOLIA = NetworkConfig(11155111, "Sepolia")
HOLESKY = NetworkConfig(17000, "Holesky", 77)

OPTIMISM = NetworkConfig(10, "Optimism", 4286263)
ARBITRUM = NetworkConfig(42161, "Arbitrum", 7654707)
BASE = NetworkConfig(8453, "Base", 5022)
ZKSYNC = NetworkConfig(324, "zkSync", 0, "0x47898B2C52C957663aE9AB46922dCec150a2272c")
MANTLE = NetworkConfig(5000, "Mantle", 304717)
LINEA = NetworkConfig(59144, "Linea", 42)

OPTIMISM_KOVAN = NetworkConfig(69, "OptimismKovan")
OPTIMISM_GOERLI = NetworkConfig(420, "OptimismGoerli")
ARBITRUM_RINKEBY = NetworkConfig(421611, "ArbitrumRinkeby")
ARBITRUM_GOERLI = NetworkConfig(421613, "ArbitrumGoerli")

BSC = NetworkConfig(56, "BSC", 15921452)
BSC_TESTNET = NetworkConfig(97, "BSCTestnet")

POLYGON = NetworkConfig(137, "Polygon", 25770160)
MUMBAI = NetworkConfig(80001, "Mumbai")
FANTOM = NetworkConfig(250, "Fantom")
FANTOM_TESTNET = NetworkConfig(4002, "FantomTestnet")
GNOSIS = NetworkConfig(100, "Gnosis")
AVALANCHE = NetworkConfig(43114, "Avalanche")
AVALANCHE_FUJI = NetworkConfig(43113, "AvalancheFuji")
AURORA = NetworkConfig(1313161554, "Aurora")
CELO = NetworkConfig(42220, "Celo")

METIS = NetworkConfig(1088, "Metis")
MOONBEAM = NetworkConfig(1284, "Moonbeam")
MOONRIVER = NetworkConfig(1285, "Moonriver")
MOONBASE_ALPHA = NetworkConfig(1287, "MoonbaseAlphaTestnet")
HARMONY = NetworkConfig(1666600000, "Harmony")
CRONOS = NetworkConfig(25, "Cronos")
PULSECHAIN = NetworkConfig(369, "PulseChain")
PULSECHAIN_TESTNET = NetworkConfig(943, "PulseChainTestnet")

THUNDERCORE = NetworkConfig(108, "Thundercore")
THUNDERCORE_TESTNET = NetworkConfig(18, "ThundercoreTestnet")
VELAS = NetworkConfig(106, "Velas")
HECO = NetworkConfig(128, "Heco")
BOBA = NetworkConfig(288, "Boba")
KCC = NetworkConfig(321, "KCC")
ASTAR = NetworkConfig(592, "Astar")
MILKOMEDA = NetworkConfig(2001, "Milkomeda")
KAVA = NetworkConfig(2222, "Kava")
ZETA = NetworkConfig(7000, "ZetaMainnet", 1632781)
CANTO = NetworkConfig(7700, "Canto")
KLAYTN = NetworkConfig(8217, "Klaytn")
EVMOS = NetworkConfig(9001, "Evmos")
EVMOS_TESTNET = NetworkConfig(9000, "EvmosTestnet")
OASIS = NetworkConfig(42262, "Oasis")
GODWOKEN = NetworkConfig(71402, "Godwoken")
GODWOKEN_TESTNET = NetworkConfig(71401, "GodwokenTestnet")

COSTON_TESTNET = NetworkConfig(16, "CostonTestnet")
SONGBIRD = NetworkConfig(19, "SongbirdCanaryNetwork")
RSK = NetworkConfig(30, "RSK")
RSK_TESTNET = NetworkConfig(31, "RSKTestnet")
KOVAN = NetworkConfig(42, "Kovan")
OKC = NetworkConfig(66, "OKC")
FUSE = NetworkConfig(122, "Fuse")
COSTON2_TESTNET = NetworkConfig(114, "Coston2Testnet")
TAIKO_MAIN = NetworkConfig(167000, "Taiko", 11269)
CYBER_TESTNET = NetworkConfig(111557560, "CyberTestnet")
CYBER = NetworkConfig(7560, "Cyber", 3413302)
STORY_ODYSSEY_TESTNET = NetworkConfig(1516, "StoryOdysseyTestnet", 14880)
MONAD_TESTNET = NetworkConfig(10143, "MonadalTestnet", 251449)
SONIC = NetworkConfig(146, "Sonic", 60)
SONIC_TESTNET = NetworkConfig(57054, "SonicTestnet", 1100)


def get_multicall_network(chain_id: int) -> NetworkConfig:
    return NetworkConfig.from_chain_id(chain_id)


def get_multicall_address(network: NetworkConfig) -> str:
    return network.multicall_address
