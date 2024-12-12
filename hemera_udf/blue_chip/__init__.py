from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera.indexer.domains.block import Block
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.token import Token, UpdateToken
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_transfer import ERC721TokenTransfer
from hemera.indexer.domains.transaction import Transaction
from hemera_udf.aci_features.domains import AllFeatureValueRecordBlueChipHolders
from hemera_udf.blue_chip.domains import BlueChipHolder

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-address-index:{__version__}` needs Hemera 1.0.0+")

value = DynamicEntityTypeRegistry.register("BLUE_CHIP")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        Block,
        Transaction,
        ERC721TokenTransfer,
        Token,
        UpdateToken,
        TokenBalance,
        CurrentTokenBalance,
        AllFeatureValueRecordBlueChipHolders,
        BlueChipHolder,
    },
)
