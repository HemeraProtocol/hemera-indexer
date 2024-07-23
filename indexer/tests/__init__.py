import os
ETHEREUM_PUBLIC_NODE_RPC_URL= os.environ.get('ETHEREUM_PUBLIC_NODE_RPC_URL', 'https://ethereum-rpc.publicnode.com')
ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL = os.environ.get('ETHEREUM_PUBLIC_NODE_DEBUG_RPC_URL', 'https://ethereum-rpc.publicnode.com')

DODO_TESTNET_PUBLIC_NODE_RPC_URL= os.environ.get('DODO_TESTNET_PUBLIC_NODE_RPC_URL', 'https://dodochain-testnet.alt.technology')

ARBITRUM_PUBLIC_NODE_RPC_URL= os.environ.get('ARBITRUM_PUBLIC_NODE_RPC_URL', 'https://arbitrum-one-rpc.publicnode.com')
ARBITRUM_TESTNET_PUBLIC_NODE_RPC_URL= os.environ.get('ARBITRUM_TESTNET_PUBLIC_NODE_RPC_URL', "https://arbitrum-sepolia.blockpi.network/v1/rpc/public")