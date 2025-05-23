from __future__ import annotations

import packaging.version

from hemera import __version__ as hemera_version

__all__ = ["__version__"]

__version__ = "0.1.0"

from hemera.common.enumeration.entity_type import DynamicEntityTypeRegistry
from hemera_udf.aave_v2.domains.aave_v2_domain import (
    AaveV2AddressCurrentD,
    AaveV2BorrowD,
    AaveV2CallRecordsD,
    AaveV2DepositD,
    AaveV2FlashLoanD,
    AaveV2LiquidationAddressCurrentD,
    AaveV2LiquidationCallD,
    AaveV2RepayD,
    AaveV2ReserveD,
    AaveV2ReserveDataCurrentD,
    AaveV2ReserveDataD,
    AaveV2TransferD,
    AaveV2WithdrawD,
)

if packaging.version.parse(packaging.version.parse(hemera_version).base_version) < packaging.version.parse("1.0.0"):
    raise RuntimeError(f"The package `hemera-modules-xxx:{__version__}` needs Hemera 1.0.0+")

value = DynamicEntityTypeRegistry.register("AAVE_V2")
DynamicEntityTypeRegistry.register_output_types(
    value,
    {
        AaveV2ReserveD,
        AaveV2DepositD,
        AaveV2WithdrawD,
        AaveV2BorrowD,
        AaveV2RepayD,
        AaveV2FlashLoanD,
        AaveV2LiquidationCallD,
        AaveV2AddressCurrentD,
        AaveV2LiquidationAddressCurrentD,
        AaveV2CallRecordsD,
        AaveV2ReserveDataD,
        AaveV2ReserveDataCurrentD,
        AaveV2TransferD,
    },
)
