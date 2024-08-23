from indexer.utils.multicall_hemera.call import Call
from indexer.utils.multicall_hemera.constants import Network
from indexer.utils.multicall_hemera.multi_call import Multicall
from indexer.utils.multicall_hemera.signature import Signature

"""
This package is derived from multicall.py https://github.com/banteg/multicall.py
While, multicall.py is build on asyncio, and uses web3.eth.call directly
Instead, this package generate bytes parameters and then call rpc in batch.
"""
