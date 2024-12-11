from common.utils.abi_code_utils import Event

clanker_token_created_event_v1 = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "tokenAddress", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "lpNftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "deployer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "fid", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "supply", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "lockerAddress", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "castHash", "type": "string"},
        ],
        "name": "TokenCreated",
        "type": "event",
    }
)

clanker_token_created_event_v0 = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "tokenAddress", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "lpNftId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "deployer", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "supply", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "_supply", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "lockerAddress", "type": "address"},
        ],
        "name": "TokenCreated",
        "type": "event",
    }
)

virtuals_token_created_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "uint256", "name": "virtualId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "dao", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "tba", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "veToken", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "lp", "type": "address"},
        ],
        "name": "NewPersona",
        "type": "event",
    }
)

larry_token_created_event = Event(
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "party", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "ethValue", "type": "uint256"},
            {
                "components": [
                    {"internalType": "uint256", "name": "totalSupply", "type": "uint256"},
                    {"internalType": "uint256", "name": "numTokensForDistribution", "type": "uint256"},
                    {"internalType": "uint256", "name": "numTokensForRecipient", "type": "uint256"},
                    {"internalType": "uint256", "name": "numTokensForLP", "type": "uint256"},
                ],
                "indexed": False,
                "internalType": "struct ERC20CreatorV3.TokenDistributionConfiguration",
                "name": "config",
                "type": "tuple",
            },
        ],
        "name": "ERC20Created",
        "type": "event",
    }
)
