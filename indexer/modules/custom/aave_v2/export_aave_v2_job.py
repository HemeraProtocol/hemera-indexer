import logging
from collections import defaultdict
from enum import Enum
from typing import Any, cast

from sqlalchemy import func
from web3.types import ABIEvent

from common.utils.abi_code_utils import AbiReader, Event
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.jobs.export_token_balances_job import encode_balance_abi_parameter
from indexer.modules.custom.aave_v2.aave_v2_processors import AaveV2Events
from indexer.modules.custom.aave_v2.domains.aave_v2_domain import (
    AaveV2AddressBalanceRecordsD,
    AaveV2AddressCurrentD,
    AaveV2BorrowD,
    AaveV2DepositD,
    AaveV2FlashLoanD,
    AaveV2LiquidationAddressCurrentD,
    AaveV2LiquidationCallD,
    AaveV2RepayD,
    AaveV2ReserveD,
    AaveV2WithdrawD,
    aave_v2_address_current_factory,
)
from indexer.modules.custom.aave_v2.models.aave_v2_address_current import AaveV2AddressCurrent
from indexer.modules.custom.aave_v2.models.aave_v2_reserve import AaveV2Reserve
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.token_fetcher import TokenFetcher

logger = logging.getLogger(__name__)


class InterestRateMode(Enum):
    STABLE = 1
    VARIABLE = 2


class ExportAaveV2Job(FilterTransactionDataJob):
    """This job extract aave_v2 related infos"""

    dependency_types = [Log]
    output_types = [
        AaveV2ReserveD,
        AaveV2DepositD,
        AaveV2WithdrawD,
        AaveV2BorrowD,
        AaveV2RepayD,
        AaveV2FlashLoanD,
        AaveV2LiquidationCallD,
        AaveV2AddressCurrentD,
        AaveV2LiquidationAddressCurrentD,
        AaveV2AddressBalanceRecordsD,
    ]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")

        self.job_conf = self.user_defined_config
        self.abi_reader = AbiReader(__file__)

        self.contract_addresses = {"POOL": self.job_conf["POOL"], "POOL_CONFIGURE": self.job_conf["POOL_CONFIGURE"]}

        self.address_set = set(self.contract_addresses.values())

        # event_name -> Event
        self.events = {}
        # sig -> processor
        self._event_processors = {}
        self._initialize_events_and_processors()

        # init relative tokens
        self.asset_reserve = {}
        self.vary_reserve = {}
        self.stable_reserve = {}
        self._read_reserve()

        self.token_fetcher = TokenFetcher(self._web3, kwargs)

    def _read_reserve(self):

        with self.db_service.get_service_session() as session:
            result = session.query(AaveV2Reserve).all()
        for rr in result:
            item = AaveV2ReserveD(
                asset=bytes_to_hex_str(rr.asset),
                a_token_address=bytes_to_hex_str(rr.a_token_address),
                stable_debt_token_address=bytes_to_hex_str(rr.stable_debt_token_address),
                variable_debt_token_address=bytes_to_hex_str(rr.variable_debt_token_address),
                interest_rate_strategy_address=bytes_to_hex_str(rr.interest_rate_strategy_address),
                block_number=rr.block_number,
                block_timestamp=rr.block_timestamp,
                transaction_hash=bytes_to_hex_str(rr.transaction_hash),
                log_index=rr.log_index,
            )
            self.asset_reserve[item.asset] = item
            self.vary_reserve[item.variable_debt_token_address] = item
            self.stable_reserve[item.stable_debt_token_address] = item

    def _initialize_events_and_processors(self):
        """Initialize events and their processors based on enum configuration"""
        for event_type in AaveV2Events:
            config = event_type.value
            contract_address = self.contract_addresses[config.contract_address_key]

            abi = self.abi_reader.get_event_abi(contract_address, config.name)
            event = Event(cast(ABIEvent, abi))

            self.events[event_type] = event
            signature = event.get_signature()
            self._event_processors[signature] = config.processor_class(event, config.data_class)

    def get_filter(self):
        topics = [event.get_signature() for event in self.events.values()]
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=list(self.contract_addresses.values()), topics=topics),
            ]
        )

    def is_aave_v2_address(self, address):
        return address in self.address_set

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        aave_records = []
        for log in logs:
            if not self.is_aave_v2_address(log.address):
                continue
            try:
                processor = self._event_processors.get(log.topic0)
                if processor is None:
                    continue
                processed_data = processor.process(log)
                aave_records.append(processed_data)
                self._collect_item(processed_data.type(), processed_data)
                if processed_data.type() == AaveV2ReserveD.type():
                    # update reserve
                    self.asset_reserve[processed_data.asset] = processed_data
                    self.vary_reserve[processed_data.variable_debt_token_address] = processed_data
                    self.stable_reserve[processed_data.stable_debt_token_address] = processed_data
            except Exception as e:
                logger.error(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}: {str(e)}")
                raise FastShutdownError(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}")

        related_address_set = set(
            ave.aave_user for ave in aave_records if hasattr(ave, "aave_user") and ave.aave_user
        ) | set(ave.on_behalf_of for ave in aave_records if hasattr(ave, "on_behalf_of") and ave.on_behalf_of)
        exists_dic = self.get_existing_address_current(list(related_address_set))

        # we need borrowed asset and its borrow mode
        address_asset_borrow = dict()
        for address in exists_dic:
            if address not in address_asset_borrow:
                address_asset_borrow[address] = dict()
            for asset in exists_dic[address]:
                acd = exists_dic[address][asset]
                address_asset_borrow[address][asset] = acd.borrow_rate_mode
        for a_record in aave_records:
            if a_record.type() == AaveV2BorrowD.type():
                if a_record.on_behalf_of not in address_asset_borrow:
                    address_asset_borrow[a_record.on_behalf_of] = dict()
                address_asset_borrow[a_record.on_behalf_of][a_record.reserve] = a_record.borrow_rate_mode

        balance_of_lis = []
        for a_record in aave_records:
            # when repay, call rpc to get debt_balance
            if a_record.type() == AaveV2RepayD.type():
                reserve = self.asset_reserve[a_record.reserve]
                borrow_rate_mode = None
                if a_record.aave_user in address_asset_borrow:
                    borrow_rate_mode = address_asset_borrow[a_record.aave_user].get(reserve.asset)
                if not borrow_rate_mode:
                    continue
                if borrow_rate_mode == InterestRateMode.STABLE.value:

                    balance_of_lis.append(
                        {
                            "address": a_record.aave_user,
                            "token_address": reserve.stable_debt_token_address,
                            "token_type": "ERC20",
                            "token_id": None,
                            "block_number": a_record.block_number,
                            "block_timestamp": a_record.block_timestamp,
                            "param_to": reserve.stable_debt_token_address,
                            "param_data": encode_balance_abi_parameter(a_record.aave_user, "ERC20", None),
                            "param_number": a_record.block_number,
                        }
                    )
                elif borrow_rate_mode == InterestRateMode.VARIABLE.value:
                    balance_of_lis.append(
                        {
                            "address": a_record.aave_user,
                            "token_address": reserve.variable_debt_token_address,
                            "token_type": "ERC20",
                            "token_id": None,
                            "block_number": a_record.block_number,
                            "block_timestamp": a_record.block_timestamp,
                            "param_to": reserve.variable_debt_token_address,
                            "param_data": encode_balance_abi_parameter(a_record.aave_user, "ERC20", None),
                            "param_number": a_record.block_number,
                        }
                    )
                else:
                    raise FastShutdownError(f"Unsupported borrow type {borrow_rate_mode}")
            elif a_record.type() == AaveV2LiquidationCallD.type():
                aave_user = a_record.aave_user
                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.asset_reserve[collateral_asset]
                balance_of_lis.append(
                    {
                        "address": aave_user,
                        "token_address": collateral_reserve.a_token_address,
                        "token_type": "ERC20",
                        "token_id": None,
                        "block_number": a_record.block_number,
                        "block_timestamp": a_record.block_timestamp,
                        "param_to": collateral_reserve.a_token_address,
                        "param_data": encode_balance_abi_parameter(aave_user, "ERC20", None),
                        "param_number": a_record.block_number,
                    }
                )
                debt_asset = a_record.debt_asset
                debt_reserve = self.asset_reserve[debt_asset]
                borrow_rate_mode = None
                if a_record.aave_user in address_asset_borrow:
                    borrow_rate_mode = address_asset_borrow[a_record.aave_user].get(debt_reserve.asset)
                if not borrow_rate_mode:
                    continue
                if borrow_rate_mode == InterestRateMode.STABLE.value:

                    balance_of_lis.append(
                        {
                            "address": aave_user,
                            "token_address": debt_reserve.stable_debt_token_address,
                            "token_type": "ERC20",
                            "token_id": None,
                            "block_number": a_record.block_number,
                            "block_timestamp": a_record.block_timestamp,
                            "param_to": debt_reserve.stable_debt_token_address,
                            "param_data": encode_balance_abi_parameter(aave_user, "ERC20", None),
                            "param_number": a_record.block_number,
                        }
                    )
                elif borrow_rate_mode == InterestRateMode.VARIABLE.value:
                    balance_of_lis.append(
                        {
                            "address": a_record.aave_user,
                            "token_address": debt_reserve.variable_debt_token_address,
                            "token_type": "ERC20",
                            "token_id": None,
                            "block_number": a_record.block_number,
                            "block_timestamp": a_record.block_timestamp,
                            "param_to": debt_reserve.variable_debt_token_address,
                            "param_data": encode_balance_abi_parameter(a_record.aave_user, "ERC20", None),
                            "param_number": a_record.block_number,
                        }
                    )
                else:
                    raise FastShutdownError(f"Unsupported borrow type {borrow_rate_mode}")

        balance_enriched_tokens = self.token_fetcher.fetch_token_balance(balance_of_lis)

        address_token_block_balance_dic = {}
        unique_set = set()
        for et in balance_enriched_tokens:
            token = et["token_address"]
            address = et["address"]
            balance = et["balance"]
            block_number = et["block_number"]
            k = (address, token, block_number)
            if k in unique_set:
                continue
            unique_set.add(k)
            self._collect_item(
                AaveV2AddressBalanceRecordsD.type(),
                AaveV2AddressBalanceRecordsD(
                    address=address,
                    token=token,
                    block_number=block_number,
                    balance=balance,
                ),
            )
            if address not in address_token_block_balance_dic:
                address_token_block_balance_dic[address] = dict()
            if token not in address_token_block_balance_dic[address]:
                address_token_block_balance_dic[address][token] = dict()
            address_token_block_balance_dic[address][token][block_number] = balance

        # enrich repay, liquidation
        for a_record in aave_records:
            if a_record.type() == AaveV2RepayD.type():
                address = a_record.aave_user
                reserve = a_record.reserve
                block_number = a_record.block_number

                borrow_rate_mode = None
                if a_record.aave_user in address_asset_borrow:
                    borrow_rate_mode = address_asset_borrow[a_record.aave_user].get(reserve)
                if not borrow_rate_mode:
                    continue
                if borrow_rate_mode == InterestRateMode.VARIABLE.value:
                    vary_token = self.asset_reserve.get(reserve).variable_debt_token_address
                    debt = address_token_block_balance_dic[address][vary_token][block_number]
                elif borrow_rate_mode == InterestRateMode.STABLE.value:
                    stable_token = self.asset_reserve.get(reserve).stable_debt_token_address
                    debt = address_token_block_balance_dic[address][stable_token][block_number]
                else:
                    raise FastShutdownError(f"Unsupported borrow type {borrow_rate_mode}")
                a_record.after_repay_debt = debt
                a_record.force_update_current = True
            elif a_record.type() == AaveV2LiquidationCallD.type():
                address = a_record.aave_user
                block_number = a_record.block_number

                debt_asset = a_record.debt_asset
                borrow_rate_mode = None
                if a_record.aave_user in address_asset_borrow:
                    borrow_rate_mode = address_asset_borrow[a_record.aave_user].get(debt_asset)
                if not borrow_rate_mode:
                    continue
                if borrow_rate_mode == InterestRateMode.VARIABLE.value:
                    vary_token = self.asset_reserve.get(debt_asset).variable_debt_token_address
                    debt = address_token_block_balance_dic[address][vary_token][block_number]
                elif borrow_rate_mode == InterestRateMode.STABLE.value:
                    stable_token = self.asset_reserve.get(debt_asset).stable_debt_token_address
                    debt = address_token_block_balance_dic[address][stable_token][block_number]
                else:
                    raise FastShutdownError(f"Unsupported borrow type {borrow_rate_mode}")

                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.asset_reserve[collateral_asset]

                a_record.debt_after_liquidation = debt
                a_record.collateral_after_liquidation = address_token_block_balance_dic[address][
                    collateral_reserve.a_token_address
                ][block_number]
                a_record.force_update_current = True
        liquidation_lis = []
        batch_result_dic = self.calculate_new_address_current(exists_dic, aave_records, liquidation_lis)
        liquidation_lis = self.merge_liquidation_lis(liquidation_lis)
        self._collect_items(AaveV2LiquidationAddressCurrentD.type(), liquidation_lis)

        address_currents = []
        for address, outer_dic in batch_result_dic.items():
            for reserve, kad in outer_dic.items():
                address_currents.append(kad)
        address_currents.sort(key=lambda x: (x.address, x.asset))
        self._collect_items(AaveV2AddressCurrentD.type(), address_currents)

        logger.info("This batch of data have processed")

    def get_existing_address_current(self, addresses):
        addresses = [ad[2:] for ad in addresses if ad and ad.startswith("0x")]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            query = session.query(AaveV2AddressCurrent).filter(
                func.encode(AaveV2AddressCurrent.address, "hex").in_(addresses)
            )
            result = query.all()
        res = {}
        for rr in result:
            item = AaveV2AddressCurrentD(
                address=bytes_to_hex_str(rr.address),
                asset=bytes_to_hex_str(rr.asset),
                supply_amount=rr.supply_amount,
                borrow_amount=rr.borrow_amount,
                borrow_rate_mode=rr.borrow_rate_mode,
                block_number=rr.block_number,
                block_timestamp=int(rr.block_timestamp.timestamp()),
            )
            if item.address not in res:
                res[item.address] = {}
            res[item.address][item.asset] = item
        return res

    def merge_liquidation_lis(self, liquidation_lis):
        # keep the newest one
        liquidation_lis.sort(key=lambda x: x.last_liquidation_time, reverse=True)
        lis = []
        unique_k_set = set()
        for li in liquidation_lis:
            k = (li.address, li.asset)
            if k not in unique_k_set:
                unique_k_set.add(k)
                lis.append(li)
        return lis

    def calculate_new_address_current(self, exists_dic, aave_records, liquidation_lis) -> Any:
        def nested_dict():
            return defaultdict(aave_v2_address_current_factory)

        res_d = defaultdict(nested_dict)
        # init res_d with exists_dic
        for address, outer_dic in exists_dic.items():
            for reserve, kad in outer_dic.items():
                res_d[address][reserve] = kad
        for action in aave_records:
            if not hasattr(action, "event_name"):
                continue
            event_name = action.event_name

            if event_name == AaveV2Events.DEPOSIT.value.name:
                user = action.on_behalf_of
                reserve = action.reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].supply_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV2Events.BORROW.value.name:
                reserve = action.reserve
                user = action.on_behalf_of
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].borrow_rate_mode = action.borrow_rate_mode
                res_d[user][reserve].borrow_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV2Events.REPAY.value.name:
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].borrow_amount = action.after_repay_debt
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV2Events.WITHDRAW.value.name:
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].supply_amount -= action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV2Events.LIQUIDATION_CALL.value.name:
                collateral_asset = action.collateral_asset
                debt_asset = action.debt_asset
                user = action.aave_user
                res_d[user][collateral_asset].asset = collateral_asset
                res_d[user][collateral_asset].address = user
                res_d[user][collateral_asset].supply_amount = action.collateral_after_liquidation
                res_d[user][collateral_asset].block_number = action.block_number
                res_d[user][collateral_asset].block_timestamp = action.block_timestamp

                res_d[user][debt_asset].asset = debt_asset
                res_d[user][debt_asset].address = user
                res_d[user][debt_asset].borrow_amount = action.debt_after_liquidation
                res_d[user][debt_asset].block_number = action.block_number
                res_d[user][debt_asset].block_timestamp = action.block_timestamp

                # record last liquidation time and amount
                liquidation_lis.append(
                    AaveV2LiquidationAddressCurrentD(
                        address=user,
                        asset=collateral_asset,
                        last_liquidation_time=action.block_timestamp,
                        last_total_value_of_liquidation=action.liquidated_collateral_amount,
                    )
                )
            else:
                continue
        return res_d
