from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera_udf.merchant_moe.domains import (
    MerchantMoeErc1155TokenCurrentHolding,
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenHolding,
    MerchantMoeErc1155TokenSupply,
    MerchantMoePool,
    MerchantMoePoolCurrentStatus,
    MerchantMoePoolRecord,
    MerchantMoeTokenBin,
    MerchantMoeTokenCurrentBin,
)

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")

value = DynamicEntityTypeRegistry.register("MERCHANTMOE")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        MerchantMoeErc1155TokenHolding,
        MerchantMoeErc1155TokenCurrentHolding,
        MerchantMoeErc1155TokenSupply,
        MerchantMoeErc1155TokenCurrentSupply,
        MerchantMoeTokenBin,
        MerchantMoeTokenCurrentBin,
        MerchantMoePool,
        MerchantMoePoolCurrentStatus,
        MerchantMoePoolRecord,
    },
)
