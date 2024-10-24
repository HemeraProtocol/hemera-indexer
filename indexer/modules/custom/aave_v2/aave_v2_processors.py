import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Type, TypeVar

from common.utils.abi_code_utils import Event
from common.utils.web3_utils import extract_eth_address
from indexer.modules.custom.aave_v2.domains.aave_v2_domain import (
    AaveV2BorrowD,
    AaveV2DepositD,
    AaveV2FlashLoanD,
    AaveV2LiquidationCallD,
    AaveV2RepayD,
    AaveV2ReserveD,
    AaveV2WithdrawD,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventProcessor(ABC):
    """Abstract base processor for handling different event types"""

    def __init__(self, event: Event, data_class: Type[T]):
        self.event = event
        self.data_class = data_class

    def process(self, log: Any) -> T:
        """Process log data with common field handling and custom processing"""
        try:
            decoded_log = self.event.decode_log(log)
            common_fields = self._extract_common_fields(log, self.event)
            specific_fields = self._process_specific_fields(log, decoded_log)
            return self.data_class(**common_fields, **specific_fields)
        except Exception as e:
            logger.error(f"Error processing {self.data_class.__name__}: {str(e)}")
            raise

    def _extract_common_fields(self, log: Any, event: Any) -> dict:
        """Extract common fields present in all events"""
        return {
            "block_number": log.block_number,
            "block_timestamp": log.block_timestamp,
            "transaction_hash": log.transaction_hash,
            "log_index": log.log_index,
            "topic0": getattr(log, "topic0", None),
            "event_name": getattr(event, "get_name", lambda: None)(),
        }

    @abstractmethod
    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        """Process event-specific fields - to be implemented by concrete processors"""
        pass


class ReserveInitProcessor(EventProcessor):
    """0x3a0ca721fc364424566385a1aa271ed508cc2c0949c2272575fb3013a163a45f"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "asset": extract_eth_address(log.topic1),
            "a_token_address": extract_eth_address(log.topic2),
            "stable_debt_token_address": decoded_log.get("stableDebtToken"),
            "variable_debt_token_address": decoded_log.get("variableDebtToken"),
            "interest_rate_strategy_address": decoded_log.get("interestRateStrategyAddress"),
        }


class DepositProcessor(EventProcessor):
    """0xde6857219544bb5b7746f48ed30be6386fefc61b2f864cacf559893bf50fd951"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "on_behalf_of": extract_eth_address(log.topic2),
            "referral": log.topic3,
            "aave_user": decoded_log.get("user"),
            "amount": decoded_log.get("amount"),
        }


class WithdrawProcessor(EventProcessor):
    """0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "amount": decoded_log.get("amount"),
        }


class BorrowProcessor(EventProcessor):
    """0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "on_behalf_of": extract_eth_address(log.topic2),
            "referral": log.topic3,
            "aave_user": decoded_log.get("user"),
            "amount": decoded_log.get("amount"),
            "borrow_rate_mode": decoded_log.get("borrowRateMode"),
            "borrow_rate": decoded_log.get("borrowRate"),
        }


class RepayProcessor(EventProcessor):
    """0xa534c8dbe71f871f9f3530e97a74601fea17b426cae02e1c5aee42c96c784051"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "repayer": extract_eth_address(log.topic3),
            "amount": decoded_log.get("amount"),
        }


class FlashLoanProcessor(EventProcessor):
    """0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "target": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "reserve": extract_eth_address(log.topic3),
            "amount": decoded_log.get("amount"),
            "premium": decoded_log.get("premium"),
            "referral": decoded_log.get("referralCode"),
        }


class LiquidationCallProcessor(EventProcessor):
    """0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "collateral_asset": extract_eth_address(log.topic1),
            "debt_asset": extract_eth_address(log.topic2),
            "aave_user": extract_eth_address(log.topic3),
            "debt_to_cover": decoded_log.get("debtToCover"),
            "liquidated_collateral_amount": decoded_log.get("liquidatedCollateralAmount"),
            "liquidator": decoded_log.get("liquidator"),
            "receive_atoken": decoded_log.get("receiveAToken"),
        }


@dataclass
class EventConfig:
    """Configuration for each event type"""

    name: str
    contract_address_key: str  # POOL or POOL_CONFIGURE
    processor_class: Type[EventProcessor]
    data_class: Type[Any]


class AaveV2Events(Enum):
    """Enum containing all Aave V2 events configuration"""

    RESERVE_INIT = EventConfig(
        name="ReserveInitialized",
        contract_address_key="POOL_CONFIGURE",
        processor_class=ReserveInitProcessor,
        data_class=AaveV2ReserveD,
    )
    DEPOSIT = EventConfig(
        name="Deposit", contract_address_key="POOL", processor_class=DepositProcessor, data_class=AaveV2DepositD
    )
    WITHDRAW = EventConfig(
        name="Withdraw", contract_address_key="POOL", processor_class=WithdrawProcessor, data_class=AaveV2WithdrawD
    )
    BORROW = EventConfig(
        name="Borrow", contract_address_key="POOL", processor_class=BorrowProcessor, data_class=AaveV2BorrowD
    )
    REPAY = EventConfig(
        name="Repay", contract_address_key="POOL", processor_class=RepayProcessor, data_class=AaveV2RepayD
    )
    FLASH_LOAN = EventConfig(
        name="FlashLoan", contract_address_key="POOL", processor_class=FlashLoanProcessor, data_class=AaveV2FlashLoanD
    )
    LIQUIDATION_CALL = EventConfig(
        name="LiquidationCall",
        contract_address_key="POOL",
        processor_class=LiquidationCallProcessor,
        data_class=AaveV2LiquidationCallD,
    )
