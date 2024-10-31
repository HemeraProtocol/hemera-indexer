import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Type, TypeVar

from common.utils.abi_code_utils import Event
from common.utils.web3_utils import extract_eth_address, to_checksum_address
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import (
    AaveV1BorrowD,
    AaveV1DepositD,
    AaveV1FlashLoanD,
    AaveV1LiquidationCallD,
    AaveV1RepayD,
    AaveV1ReserveD,
    AaveV1WithdrawD,
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
        try:
            decoded_log = self.event.decode_log(log)
            common_fields = self._extract_common_fields(log, self.event)
            specific_fields = self._process_specific_fields(log, decoded_log)
            return self.data_class(**common_fields, **specific_fields)
        except Exception as e:
            logger.error(f"Error processing {self.data_class.__name__}: {str(e)}")
            raise

    def _extract_common_fields(self, log: Any, event: Any) -> dict:
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
        pass


class BaseReserveProcessor(EventProcessor):

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
    """0xc12c57b1c73a2c3a2ea4613e9476abb3d8d146857aab7329e24243fb59710c82"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "on_behalf_of": extract_eth_address(log.topic2),
            "referral": log.topic3,
            "amount": decoded_log.get("_amount"),
        }


class WithdrawProcessor(EventProcessor):
    """0x9c4ed599cd8555b9c1e8cd7643240d7d71eb76b792948c49fcb4d411f7b6b3c6"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "reserve": extract_eth_address(log.topic1),
            "aave_user": extract_eth_address(log.topic2),
            "amount": decoded_log.get("_amount"),
        }


class BorrowProcessor(EventProcessor):
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
    contract_address_key: str
    processor_class: Type[EventProcessor]
    data_class: Type[Any]


class AaveV1Events(Enum):
    """Enum containing all Aave V2 events configuration"""

    RESERVE_INIT = EventConfig(
        name="ReserveInitialized",
        contract_address_key="INIT_PROXY",
        processor_class=ReserveInitProcessor,
        data_class=AaveV1ReserveD,
    )

    DEPOSIT = EventConfig(
        name="Deposit", contract_address_key="POOL_V1", processor_class=DepositProcessor, data_class=AaveV1DepositD
    )

    WITHDRAW = EventConfig(
        name="RedeemUnderlying",
        contract_address_key="POOL_V1",
        processor_class=WithdrawProcessor,
        data_class=AaveV1WithdrawD,
    )

    BORROW = EventConfig(
        name="Borrow", contract_address_key="POOL_V1", processor_class=BorrowProcessor, data_class=AaveV1BorrowD
    )

    REPAY = EventConfig(
        name="Repay", contract_address_key="POOL_V1", processor_class=RepayProcessor, data_class=AaveV1RepayD
    )
    FLASH_LOAN = EventConfig(
        name="FlashLoan",
        contract_address_key="POOL_V1",
        processor_class=FlashLoanProcessor,
        data_class=AaveV1FlashLoanD,
    )
    LIQUIDATION_CALL = EventConfig(
        name="LiquidationCall",
        contract_address_key="POOL_V1",
        processor_class=LiquidationCallProcessor,
        data_class=AaveV1LiquidationCallD,
    )
