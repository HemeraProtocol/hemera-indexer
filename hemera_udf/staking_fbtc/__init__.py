"""
Not only index FBTC, but also cmETH and even other tokens
"""

from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")
