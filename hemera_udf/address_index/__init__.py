from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera.indexer.domains.block import Block
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token import Token
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.domains.transaction import Transaction
from hemera_udf.address_index.domains import *

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")

value = DynamicEntityTypeRegistry.register("ADDRESS_INDEX")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        Block,
        Transaction,
        Log,
        Token,
        ERC20TokenTransfer,
        ERC721TokenTransfer,
        ERC1155TokenTransfer,
        AddressNftTransfer,
        AddressTokenHolder,
        AddressTokenTransfer,
        TokenAddressNftInventory,
        AddressTransaction,
        AddressNft1155Holder,
        AddressContractOperation,
        AddressInternalTransaction,
    },
)
