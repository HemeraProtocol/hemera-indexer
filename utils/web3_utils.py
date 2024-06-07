from web3 import Web3
from web3.middleware import geth_poa_middleware


def build_web3(provider):
    w3 = Web3(provider)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def verify_0_address(address):
    return set(address[2:]) == {'0'}
