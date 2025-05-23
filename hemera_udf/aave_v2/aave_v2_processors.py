import logging
from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from hemera.common.utils.abi_code_utils import Event
from hemera.common.utils.web3_utils import extract_eth_address
from hemera.indexer.utils.multicall_hemera import Call
from hemera_udf.aave_v2.abi.abi import DECIMALS_FUNCTIOIN, SYMBOL_FUNCTIOIN

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventProcessor(ABC):
    """Abstract base processor for handling different event types"""

    def __init__(self, event: Event, data_class: Type[T], multicall_helper=None):
        self.event = event
        self.data_class = data_class
        self.multicall_helper = multicall_helper

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

    def _get_token_info(self, address: str) -> dict:
        decimals_call = Call(target=address, function_abi=DECIMALS_FUNCTIOIN, block_number="latest")
        symbol_call = Call(target=address, function_abi=SYMBOL_FUNCTIOIN, block_number="latest")
        self.multicall_helper.execute_calls([decimals_call, symbol_call])
        return {"decimals": decimals_call.returns["decimals"], "symbol": symbol_call.returns["symbol"]}

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


class RepayProcessor(EventProcessor):
    """0x4cdde6e09bb755c9a5589ebaec640bbfedff1362d4b255ebf8339782b9942faa"""

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


class ReserveDataUpdateProcessor(EventProcessor):
    """0x804c9b842b2748a22bb64b345453a3de7ca54a6ca45ce00d415894979e22897a"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "asset": extract_eth_address(log.topic1),
            "liquidity_rate": decoded_log.get("liquidityRate"),
            "stable_borrow_rate": decoded_log.get("stableBorrowRate"),
            "variable_borrow_rate": decoded_log.get("variableBorrowRate"),
            "liquidity_index": decoded_log.get("liquidityIndex"),
            "variable_borrow_index": decoded_log.get("variableBorrowIndex"),
        }


class TransferProcessor(EventProcessor):
    """0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"""

    def _process_specific_fields(self, log: Any, decoded_log: Any) -> dict:
        return {
            "a_token": log.address,
            "amount": decoded_log.get("value"),
            "aave_from": extract_eth_address(log.topic1),
            "aave_to": extract_eth_address(log.topic2),
        }
