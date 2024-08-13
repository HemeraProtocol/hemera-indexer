import threading

UNISWAP_V2_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"indexed": False, "internalType": "uint112", "name": "reserve1", "type": "uint112"},
        ],
        "name": "Sync",
        "type": "event",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "factory",
        "outputs": [{"internalType": "address", "name": "factory", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "pair", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "length", "type": "uint256"},
        ],
        "name": "PairCreated",
        "type": "event",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


class ThreadSafeList:
    def __init__(self):
        self.list = []
        self.lock = threading.Lock()

    def add_items(self, items):
        with self.lock:
            self.list.extend(items)

    def clear_list(self):
        with self.lock:
            self.list.clear()

    def __iter__(self):
        with self.lock:
            return iter(self.list.copy())
