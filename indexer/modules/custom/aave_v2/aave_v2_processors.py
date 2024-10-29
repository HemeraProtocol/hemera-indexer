import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Type, TypeVar

from common.utils.abi_code_utils import Event
from common.utils.web3_utils import extract_eth_address, to_checksum_address
from indexer.modules.custom.aave_v2.domains.aave_v2_domain import (
    AaveV2BorrowD,
    AaveV2DepositD,
    AaveV2FlashLoanD,
    AaveV2LiquidationCallD,
    AaveV2RepayD,
    AaveV2ReserveD,
    AaveV2ReserveV1D,
    AaveV2WithdrawD,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventProcessor(ABC):
    """Abstract base processor for handling different event types"""

    def __init__(self, event: Event, data_class: Type[T], web3=None):
        self.event = event
        self.data_class = data_class
        self.web3 = web3

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


class BaseReserveProcessor(EventProcessor):
    """Base class for reserve initialization processors"""

    def __init__(self, event: Event, data_class: Type[T], web3=None):
        super().__init__(event, data_class, web3)
        self.abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
        ]

    def _get_token_info(self, address: str) -> dict:
        """Get token decimals and symbol"""
        contract = self.web3.eth.contract(abi=self.abi, address=to_checksum_address(address))
        return {"decimals": contract.functions.decimals().call(), "symbol": contract.functions.symbol().call()}


class ReserveInitProcessor(BaseReserveProcessor):
    """0x3a0ca721fc364424566385a1aa271ed508cc2c0949c2272575fb3013a163a45f"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        asset = extract_eth_address(log.topic1)
        if asset == "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2":
            asset_info = {
                "symbol": "MKR",
                "decimals": 18,
            }
        else:
            asset_info = self._get_token_info(asset)

        a_token = extract_eth_address(log.topic2)
        a_token_info = self._get_token_info(a_token)

        stable_debt_token = decoded_log.get("stableDebtToken")
        stable_debt_info = self._get_token_info(stable_debt_token)

        variable_debt_token = decoded_log.get("variableDebtToken")
        variable_debt_info = self._get_token_info(variable_debt_token)

        return {
            "asset": asset,
            "asset_symbol": asset_info["symbol"],
            "asset_decimals": asset_info["decimals"],
            "a_token_address": a_token,
            "a_token_symbol": a_token_info["symbol"],
            "a_token_decimals": a_token_info["decimals"],
            "stable_debt_token_address": stable_debt_token,
            "stable_debt_token_decimals": stable_debt_info["decimals"],
            "stable_debt_token_symbol": stable_debt_info["symbol"],
            "variable_debt_token_address": variable_debt_token,
            "variable_debt_token_symbol": variable_debt_info["symbol"],
            "variable_debt_token_decimals": variable_debt_info["decimals"],
            "interest_rate_strategy_address": decoded_log.get("interestRateStrategyAddress"),
        }


class ReserveInitProcessorV1(BaseReserveProcessor):
    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        asset = extract_eth_address(log.topic1)
        if asset == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
            asset_info = {
                "symbol": "_ETH",
                "decimals": 18,
            }
        elif asset == "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2":
            asset_info = {
                "symbol": "MKR",
                "decimals": 18,
            }
        else:
            asset_info = self._get_token_info(asset)

        a_token = extract_eth_address(log.topic2)
        a_token_info = self._get_token_info(a_token)

        return {
            "asset": asset,
            "asset_symbol": asset_info["symbol"],
            "asset_decimals": asset_info["decimals"],
            "a_token_address": a_token,
            "a_token_symbol": a_token_info["symbol"],
            "a_token_decimals": a_token_info["decimals"],
            "interest_rate_strategy_address": decoded_log.get("_interestRateStrategyAddress"),
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


class DepositProcessorV1(EventProcessor):
    """0xc12c57b1c73a2c3a2ea4613e9476abb3d8d146857aab7329e24243fb59710c82"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "on_behalf_of": extract_eth_address(log.topic2),
            "referral": log.topic3,
            "amount": decoded_log.get("_amount"),
        }


class WithdrawProcessor(EventProcessor):
    """0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "amount": decoded_log.get("amount"),
        }


class WithdrawProcessorV1(EventProcessor):
    """0x9c4ed599cd8555b9c1e8cd7643240d7d71eb76b792948c49fcb4d411f7b6b3c6"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "amount": decoded_log.get("_amount"),
        }


class BorrowProcessor(EventProcessor):
    """0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b"""

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


class BorrowProcessorV1(EventProcessor):
    """0x1e77446728e5558aa1b7e81e0cdab9cc1b075ba893b740600c76a315c2caa553"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "on_behalf_of": extract_eth_address(log.topic2),
            "referral": log.topic3,
            "amount": decoded_log.get("_amount"),
            "borrow_rate_mode": decoded_log.get("_borrowRateMode"),
            "borrow_rate": decoded_log.get("_borrowRate"),
        }


class RepayProcessor(EventProcessor):
    """0x4cdde6e09bb755c9a5589ebaec640bbfedff1362d4b255ebf8339782b9942faa"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "repayer": extract_eth_address(log.topic3),
            "amount": decoded_log.get("amount"),
        }


class RepayProcessorV1(EventProcessor):
    """0xb718f0b14f03d8c3adf35b15e3da52421b042ac879e5a689011a8b1e0036773d"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "repayer": extract_eth_address(log.topic3),
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


class LiquidationCallProcessorV1(EventProcessor):
    """0x56864757fd5b1fc9f38f5f3a981cd8ae512ce41b902cf73fc506ee369c6bc237"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "collateral_asset": extract_eth_address(log.topic1),
            # a little uncertain
            "debt_asset": extract_eth_address(log.topic2),
            "aave_user": extract_eth_address(log.topic3),
            "liquidated_collateral_amount": decoded_log.get("_liquidatedCollateralAmount"),
            "liquidator": decoded_log.get("_liquidator"),
            "receive_atoken": decoded_log.get("_receiveAToken"),
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
    RESERVE_INIT_V1 = EventConfig(
        name="ReserveInitialized",
        contract_address_key="POOL_PROXY",
        processor_class=ReserveInitProcessorV1,
        data_class=AaveV2ReserveV1D,
    )
    DEPOSIT = EventConfig(
        name="Deposit", contract_address_key="POOL_V2", processor_class=DepositProcessor, data_class=AaveV2DepositD
    )

    DEPOSIT_V1 = EventConfig(
        name="Deposit", contract_address_key="POOL_V1", processor_class=DepositProcessorV1, data_class=AaveV2DepositD
    )
    WITHDRAW = EventConfig(
        name="Withdraw", contract_address_key="POOL_V2", processor_class=WithdrawProcessor, data_class=AaveV2WithdrawD
    )
    WITHDRAW_V1 = EventConfig(
        name="RedeemUnderlying",
        contract_address_key="POOL_V1",
        processor_class=WithdrawProcessorV1,
        data_class=AaveV2WithdrawD,
    )
    BORROW = EventConfig(
        name="Borrow", contract_address_key="POOL_V2", processor_class=BorrowProcessor, data_class=AaveV2BorrowD
    )
    BORROW_V1 = EventConfig(
        name="Borrow", contract_address_key="POOL_V1", processor_class=BorrowProcessorV1, data_class=AaveV2BorrowD
    )
    REPAY = EventConfig(
        name="Repay", contract_address_key="POOL_V2", processor_class=RepayProcessor, data_class=AaveV2RepayD
    )
    Repay_V1 = EventConfig(
        name="Repay", contract_address_key="POOL_V1", processor_class=RepayProcessorV1, data_class=AaveV2RepayD
    )
    FLASH_LOAN = EventConfig(
        name="FlashLoan",
        contract_address_key="POOL_V2",
        processor_class=FlashLoanProcessor,
        data_class=AaveV2FlashLoanD,
    )
    LIQUIDATION_CALL = EventConfig(
        name="LiquidationCall",
        contract_address_key="POOL_V2",
        processor_class=LiquidationCallProcessor,
        data_class=AaveV2LiquidationCallD,
    )
    LIQUIDATION_CALL_V1 = EventConfig(
        name="LiquidationCall",
        contract_address_key="POOL_V1",
        processor_class=LiquidationCallProcessorV1,
        data_class=AaveV2LiquidationCallD,
    )
