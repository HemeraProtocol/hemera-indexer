from hemera.common.utils.abi_code_utils import Function

get_total_shares_func = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "getTotalShares",
        "outputs": [{"name": "totalShares", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

get_buffered_ether_func = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "getBufferedEther",
        "outputs": [{"name": "bufferedEther", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

get_beacon_stat_func = Function(
    {
        "constant": True,
        "inputs": [],
        "name": "getBeaconStat",
        "outputs": [
            {"name": "depositedValidators", "type": "uint256"},
            {"name": "beaconValidators", "type": "uint256"},
            {"name": "beaconBalance", "type": "uint256"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)

get_shares_func = Function(
    {
        "constant": True,
        "inputs": [{"name": "_account", "type": "address"}],
        "name": "sharesOf",
        "outputs": [{"name": "shares", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
)
