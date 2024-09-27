from ens.auto import ns
from ens.utils import address_to_reverse_domain


def get_reverse_node(address):
    address = address_to_reverse_domain(address)
    return ns.namehash(address)
