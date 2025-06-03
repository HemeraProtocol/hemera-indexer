from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera_udf.swap.domains.swap_event_domain import UniswapV3SwapEvent
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolFromSwapEvent,
    UniswapV3PoolFromToken,
    UniswapV3PoolPrice,
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
)

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")


value = DynamicEntityTypeRegistry.register("UNISWAP_V3")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        UniswapV3Pool,
        UniswapV3PoolPrice,
        UniswapV3PoolCurrentPrice,
        UniswapV3SwapEvent,
        UniswapV3PoolFromSwapEvent,
        UniswapV3Token,
        UniswapV3TokenDetail,
        UniswapV3TokenCurrentStatus,
        UniswapV3PoolFromToken,
    },
)
