from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import *

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-uniswap-v4:{__version__}` needs Hemera 1.0.0+")


value = DynamicEntityTypeRegistry.register("UNISWAP_V4")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        UniswapV4Pool,
        UniswapV4PoolPrice,
        UniswapV4PoolCurrentPrice,
        UniswapV4SwapEvent,
        UniswapV4Hook,
    },
)
