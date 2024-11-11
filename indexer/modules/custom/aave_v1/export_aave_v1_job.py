import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import func

from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.aave_v1.aave_v1_processors import (
    BorrowProcessor,
    DepositProcessor,
    FlashLoanProcessor,
    LiquidationCallProcessor,
    RepayProcessor,
    ReserveInitProcessor,
    WithdrawProcessor,
)
from indexer.modules.custom.aave_v1.abi.abi import (
    BORROW_EVENT,
    DEPOSIT_EVENT,
    FLUSH_LOAN_EVENT,
    LIQUIDATION_CALL_EVENT,
    REDEEM_EVENT,
    REPAY_EVENT,
    RESERVE_INITIALIZED_EVENT,
)
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import (
    AaveV1AddressCurrentD,
    AaveV1BorrowD,
    AaveV1CallRecordsD,
    AaveV1DepositD,
    AaveV1FlashLoanD,
    AaveV1LiquidationAddressCurrentD,
    AaveV1LiquidationCallD,
    AaveV1RepayD,
    AaveV1ReserveD,
    AaveV1WithdrawD,
    aave_v2_address_current_factory,
)
from indexer.modules.custom.aave_v1.models.aave_v1_address_current import AaveV1AddressCurrent
from indexer.modules.custom.aave_v1.models.aave_v1_reserve import AaveV1Reserve
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)

GET_USRE_BALANCE = "getUserBorrowBalances(address,address)(uint256,uint256,uint256)"
BALANCE_OF = "balanceOf(address)(uint256)"


class ExportAaveV1Job(FilterTransactionDataJob):
    """This job extract aave_v2 related infos"""

    dependency_types = [Log]
    output_types = [
        AaveV1ReserveD,
        AaveV1DepositD,
        AaveV1WithdrawD,
        AaveV1BorrowD,
        AaveV1RepayD,
        AaveV1FlashLoanD,
        AaveV1LiquidationCallD,
        AaveV1AddressCurrentD,
        AaveV1LiquidationAddressCurrentD,
        AaveV1CallRecordsD,
    ]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")

        self.contract_addresses = {
            "POOL_V1": self.user_defined_config["POOL_V1"],
            "INIT_PROXY": self.user_defined_config["INIT_PROXY"],
            "POOL": self.user_defined_config["POOL"],
            "POOL_V1_CORE": self.user_defined_config["POOL_V1_CORE"],
        }

        self.address_set = set(self.contract_addresses.values())

        # sig -> processor
        self._event_processors = {}
        self._initialize_events_and_processors()

        # init relative tokens
        self.reserve_dic = {}
        self._read_reserve()

        self.multicall_helper = MultiCallHelper(self._web3, kwargs)

    def _read_reserve(self):

        with self.db_service.get_service_session() as session:
            result = session.query(AaveV1Reserve).all()
        for rr in result:
            item = AaveV1ReserveD(
                asset=bytes_to_hex_str(rr.asset),
                asset_symbol=rr.asset_symbol,
                asset_decimals=rr.asset_decimals,
                a_token_address=bytes_to_hex_str(rr.a_token_address),
                a_token_symbol=rr.a_token_symbol,
                a_token_decimals=rr.a_token_decimals,
                interest_rate_strategy_address=(
                    bytes_to_hex_str(rr.interest_rate_strategy_address) if rr.interest_rate_strategy_address else None
                ),
                block_number=rr.block_number,
                block_timestamp=rr.block_timestamp,
                transaction_hash=bytes_to_hex_str(rr.transaction_hash) if rr.transaction_hash else None,
                log_index=rr.log_index,
            )
            self.reserve_dic[item.asset] = item

    def _initialize_events_and_processors(self):
        processors = [
            ReserveInitProcessor(RESERVE_INITIALIZED_EVENT, AaveV2ReserveD, multicall_helper=self.multicall_helper),
            DepositProcessor(DEPOSIT_EVENT, AaveV2DepositD),
            WithdrawProcessor(REDEEM_EVENT, AaveV2WithdrawD),
            BorrowProcessor(BORROW_EVENT, AaveV2BorrowD),
            RepayProcessor(REPAY_EVENT, AaveV2RepayD),
            FlashLoanProcessor(FLUSH_LOAN_EVENT, AaveV2FlashLoanD),
            LiquidationCallProcessor(LIQUIDATION_CALL_EVENT, AaveV2LiquidationCallD),
        ]
        self._event_processors[signature] = config.processor_class(event, config.data_class, self._web3)

    def get_filter(self):
        topics = [event.get_signature() for event in self.events.values()]
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=list(self.contract_addresses.values()), topics=topics),
            ]
        )

    def is_aave_v1_address(self, address):
        return address in self.address_set

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        aave_records = []
        reserve_init_lis = []
        for log in logs:
            if not self.is_aave_v1_address(log.address):
                continue
            try:
                processor = self._event_processors.get(log.topic0)
                if processor is None:
                    continue
                processed_data = processor.process(log)
                if processed_data.type() == AaveV1ReserveD.type():
                    self.reserve_dic[processed_data.asset] = processed_data
                    reserve_init_lis.append(processed_data)
                    continue
                self._collect_item(processed_data.type(), processed_data)
                aave_records.append(processed_data)
            except Exception as e:
                logger.error(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}: {str(e)}")
                raise FastShutdownError(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}")

        related_address_set = set(
            ave.aave_user for ave in aave_records if hasattr(ave, "aave_user") and ave.aave_user
        ) | set(ave.on_behalf_of for ave in aave_records if hasattr(ave, "on_behalf_of") and ave.on_behalf_of)
        exists_dic = self.get_existing_address_current(list(related_address_set))

        eth_call_lis = []
        for a_record in aave_records:
            # when repay, call rpc to get debt_balance
            if a_record.type() == AaveV1RepayD.type():
                eth_call_lis.append(
                    Call(
                        self.contract_addresses["POOL_V1_CORE"],
                        [
                            GET_USRE_BALANCE,
                            a_record.reserve,
                            a_record.aave_user,
                        ],
                        block_id=a_record.block_number,
                    )
                )
            elif a_record.type() == AaveV1WithdrawD.type():
                eth_call_lis.append(
                    Call(
                        self.contract_addresses["POOL_V1_CORE"],
                        [
                            GET_USRE_BALANCE,
                            a_record.reserve,
                            a_record.aave_user,
                        ],
                        block_id=a_record.block_number,
                    )
                )

            elif a_record.type() == AaveV1RepayD.type():
                eth_call_lis.append(
                    Call(
                        target=self.contract_addresses["POOL_V1_CORE"],
                        function=[GET_USRE_BALANCE, a_record.reserve, a_record.aave_user],
                        block_id=a_record.block_number,
                    )
                )
            elif a_record.type() == AaveV1LiquidationCallD.type():
                aave_user = a_record.aave_user
                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.reserve_dic[collateral_asset]
                eth_call_lis.append(
                    Call(
                        target=collateral_reserve.a_token_address,
                        function=[BALANCE_OF, aave_user],
                        block_id=a_record.block_number,
                    )
                )
                debt_asset = a_record.debt_asset
                debt_reserve = self.reserve_dic[debt_asset]

                eth_call_lis.append(
                    Call(
                        target=debt_reserve.stable_debt_token_address,
                        function=[BALANCE_OF, aave_user],
                        block_id=a_record.block_number,
                    )
                )

        enriched_eth_call_lis = self.multicall_helper.execute_calls(eth_call_lis)

        address_token_block_balance_dic = {}
        address_asset_block_borrow_balance_dic = {}

        unique_set = set()
        for cl in enriched_eth_call_lis:
            k = (cl.target.lower(), cl.block_id, cl.function, ",".join(cl.args))
            if k in unique_set:
                continue
            unique_set.add(k)
            self._collect_item(
                AaveV1CallRecordsD.type(),
                AaveV1CallRecordsD(
                    target=cl.target.lower(),
                    params=",".join(cl.args),
                    function=cl.function,
                    block_number=cl.block_id,
                    result=str(cl.returns),
                ),
            )
            token = cl.target.lower()
            block_number = cl.block_id
            if cl.function.startswith("getUserBorrowBalances"):
                address = cl.args[1]
                asset = cl.args[0]
                if address not in address_asset_block_borrow_balance_dic:
                    address_asset_block_borrow_balance_dic[address] = dict()
                if asset not in address_asset_block_borrow_balance_dic[address]:
                    address_asset_block_borrow_balance_dic[address][asset] = dict()
                address_asset_block_borrow_balance_dic[address][asset][block_number] = cl.returns
            else:
                address = cl.args[0]
                if address not in address_token_block_balance_dic:
                    address_token_block_balance_dic[address] = dict()
                if token not in address_token_block_balance_dic[address]:
                    address_token_block_balance_dic[address][token] = dict()
                address_token_block_balance_dic[address][token][block_number] = cl.returns

        # enrich repay, liquidation
        for a_record in aave_records:
            if a_record.type() == AaveV1RepayD.type():
                address = a_record.aave_user
                reserve = a_record.reserve
                block_number = a_record.block_number

                a_record.after_repay_debt = address_token_block_balance_dic[address][reserve][block_number]
                a_record.force_update_current = True
            elif a_record.type() == AaveV1LiquidationCallD.type():
                address = a_record.aave_user
                block_number = a_record.block_number

                debt_asset = a_record.debt_asset

                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.reserve_dic[collateral_asset]

                a_record.debt_after_liquidation = address_token_block_balance_dic[address][debt_asset][
                    collateral_asset
                ][block_number]
                a_record.collateral_after_liquidation = address_token_block_balance_dic[address][
                    collateral_reserve.a_token_address
                ][block_number]
                a_record.force_update_current = True
        liquidation_lis = []
        batch_result_dic = self.calculate_new_address_current(exists_dic, aave_records, liquidation_lis)
        liquidation_lis = self.merge_liquidation_lis(liquidation_lis)
        self._collect_items(AaveV1LiquidationAddressCurrentD.type(), liquidation_lis)
        reserve_init_lis = self.merge_reserve_init_lis(reserve_init_lis)
        self._collect_items(AaveV1ReserveD.type(), reserve_init_lis)
        address_currents = []
        for address, outer_dic in batch_result_dic.items():
            for reserve, kad in outer_dic.items():
                address_currents.append(kad)
        address_currents.sort(key=lambda x: (x.address, x.asset))
        self._collect_items(AaveV1AddressCurrentD.type(), address_currents)

        logger.info("This batch of data have processed")

    def get_existing_address_current(self, addresses):
        addresses = [ad[2:] for ad in addresses if ad and ad.startswith("0x")]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            query = session.query(AaveV1AddressCurrent).filter(
                func.encode(AaveV1AddressCurrent.address, "hex").in_(addresses)
            )
            result = query.all()
        res = {}
        for rr in result:
            item = AaveV1AddressCurrentD(
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

    def merge_reserve_init_lis(self, reserve_init_lis):
        # keep the newest one
        reserve_init_lis.sort(key=lambda x: x.block_timestamp, reverse=True)
        lis = []
        unique_k_set = set()
        for li in reserve_init_lis:
            k = li.asset
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

            if event_name == AaveV1Events.DEPOSIT.value.name:
                user = action.on_behalf_of
                reserve = action.reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                if res_d[user][reserve].supply_amount is None:
                    res_d[user][reserve].supply_amount = action.amount
                else:
                    res_d[user][reserve].supply_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV1Events.BORROW.value.name:
                reserve = action.reserve
                user = action.on_behalf_of
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].borrow_rate_mode = action.borrow_rate_mode
                if res_d[user][reserve].borrow_amount is None:
                    res_d[user][reserve].borrow_amount = action.amount
                else:
                    res_d[user][reserve].borrow_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV1Events.REPAY.value.name:
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].borrow_amount = action.after_repay_debt
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV1Events.WITHDRAW.value.name:
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                if res_d[user][reserve].supply_amount is None:
                    res_d[user][reserve].supply_amount = action.amount
                else:
                    res_d[user][reserve].supply_amount -= action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV1Events.LIQUIDATION_CALL.value.name:
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
                    AaveV1LiquidationAddressCurrentD(
                        address=user,
                        asset=collateral_asset,
                        last_liquidation_time=action.block_timestamp,
                        last_total_value_of_liquidation=action.liquidated_collateral_amount,
                    )
                )
            else:
                continue
        return res_d
