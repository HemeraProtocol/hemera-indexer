import logging
from collections import defaultdict

from hemera.common.utils.exception_control import FastShutdownError
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.log import Log
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.collection_utils import merge_dataclasses
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.aave_v2.aave_v2_processors import (
    BorrowProcessor,
    DepositProcessor,
    FlashLoanProcessor,
    LiquidationCallProcessor,
    RepayProcessor,
    ReserveDataUpdateProcessor,
    ReserveInitProcessor,
    TransferProcessor,
    WithdrawProcessor,
)
from hemera_udf.aave_v2.abi.abi import (
    BORROW_EVENT,
    DEPOSIT_EVENT,
    FLUSH_LOAN_EVENT,
    LIQUIDATION_CALL_EVENT,
    PRINCIPAL_BALANCE_OF_FUNCTION,
    REPAY_EVENT,
    RESERVE_DATA_UPDATED_EVENT,
    RESERVE_INITIALIZED_EVENT,
    SCALED_BALANCE_OF_FUNCTION,
    TRANSFER_EVENT,
    WITHDRAW_EVENT,
)
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
    aave_v2_address_current_factory,
)
from hemera_udf.aave_v2.models.aave_v2_reserve import AaveV2Reserve

logger = logging.getLogger(__name__)


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
        AaveV2CallRecordsD,
        AaveV2ReserveDataD,
        AaveV2TransferD,
        AaveV2ReserveDataCurrentD,
    ]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")
        self.contract_addresses = {
            "POOL_V2": self.user_defined_config["POOL_V2"],
            "POOL_CONFIGURE": self.user_defined_config["POOL_CONFIGURE"],
        }

        self.multicall_helper = MultiCallHelper(self._web3, kwargs)

        # sig -> processor
        self._event_processors = {}
        self._initialize_events_and_processors()

        # init relative tokens
        self.reserve_dic = {}
        self.a_token_reserve_dic = {}
        self.vary_debt_reserve_dic = {}
        self.stable_debt_reserve_dic = {}
        self._read_reserve()

        self.address_set = set(
            list(self.a_token_reserve_dic.keys())
            + list(self.contract_addresses.values())
            + list(self.vary_debt_reserve_dic)
            + list(self.stable_debt_reserve_dic)
        )

    def _read_reserve(self):

        with self.db_service.get_service_session() as session:
            result = session.query(AaveV2Reserve).all()
        for rr in result:
            item = AaveV2ReserveD(
                asset=bytes_to_hex_str(rr.asset),
                asset_symbol=rr.asset_symbol,
                asset_decimals=rr.asset_decimals,
                a_token_address=bytes_to_hex_str(rr.a_token_address),
                a_token_symbol=rr.a_token_symbol,
                a_token_decimals=rr.a_token_decimals,
                stable_debt_token_address=(
                    bytes_to_hex_str(rr.stable_debt_token_address) if rr.stable_debt_token_address else None
                ),
                stable_debt_token_symbol=rr.stable_debt_token_symbol,
                stable_debt_token_decimals=rr.stable_debt_token_decimals,
                variable_debt_token_address=(
                    bytes_to_hex_str(rr.variable_debt_token_address) if rr.variable_debt_token_address else None
                ),
                variable_debt_token_symbol=rr.variable_debt_token_symbol,
                variable_debt_token_decimals=rr.variable_debt_token_decimals,
                interest_rate_strategy_address=(
                    bytes_to_hex_str(rr.interest_rate_strategy_address) if rr.interest_rate_strategy_address else None
                ),
                block_number=rr.block_number,
                block_timestamp=rr.block_timestamp,
                transaction_hash=bytes_to_hex_str(rr.transaction_hash) if rr.transaction_hash else None,
                log_index=rr.log_index,
            )
            self.reserve_dic[item.asset] = item
            self.vary_debt_reserve_dic[item.variable_debt_token_address] = item
            self.stable_debt_reserve_dic[item.stable_debt_token_address] = item
            self.a_token_reserve_dic[item.a_token_address] = item

    def _initialize_events_and_processors(self):
        processors = [
            ReserveInitProcessor(RESERVE_INITIALIZED_EVENT, AaveV2ReserveD, multicall_helper=self.multicall_helper),
            DepositProcessor(DEPOSIT_EVENT, AaveV2DepositD),
            WithdrawProcessor(WITHDRAW_EVENT, AaveV2WithdrawD),
            BorrowProcessor(BORROW_EVENT, AaveV2BorrowD),
            RepayProcessor(REPAY_EVENT, AaveV2RepayD),
            FlashLoanProcessor(FLUSH_LOAN_EVENT, AaveV2FlashLoanD),
            LiquidationCallProcessor(LIQUIDATION_CALL_EVENT, AaveV2LiquidationCallD),
            ReserveDataUpdateProcessor(RESERVE_DATA_UPDATED_EVENT, AaveV2ReserveDataD),
            TransferProcessor(TRANSFER_EVENT, AaveV2TransferD),
        ]
        self._event_processors = {p.event.get_signature(): p for p in processors}

    def get_filter(self):
        topics = [p for p in self._event_processors.keys()]
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=list(self.address_set),
                    topics=topics,
                ),
            ]
        )

    def is_aave_v2_address(self, address):
        return address in self.address_set

    def update_address_current(self, aave_records, address_token_block_balance_dic):
        def nested_dict():
            return defaultdict(aave_v2_address_current_factory)

        res_d = defaultdict(nested_dict)
        for a_record in aave_records:
            if a_record.type() == AaveV2WithdrawD.type() or a_record.type() == AaveV2DepositD.type():
                reserve = self.reserve_dic[a_record.reserve]
                address = a_record.aave_user
                after = address_token_block_balance_dic[address][reserve.a_token_address][a_record.block_number]

                res_d[address][reserve.asset].address = a_record.aave_user
                res_d[address][reserve.asset].asset = reserve.asset
                res_d[address][reserve.asset].block_number = a_record.block_number
                res_d[address][reserve.asset].block_timestamp = a_record.block_timestamp
                res_d[address][reserve.asset].supply_amount = after

            elif a_record.type() == AaveV2TransferD.type():
                # a_token
                reserve = self.a_token_reserve_dic.get(a_record.a_token)
                if reserve:
                    aave_from = a_record.aave_from
                    after_transfer = address_token_block_balance_dic[aave_from][reserve.a_token_address][
                        a_record.block_number
                    ]
                    res_d[aave_from][reserve.asset].address = aave_from
                    res_d[aave_from][reserve.asset].asset = reserve.asset
                    res_d[aave_from][reserve.asset].block_number = a_record.block_number
                    res_d[aave_from][reserve.asset].block_timestamp = a_record.block_timestamp
                    res_d[aave_from][reserve.asset].supply_amount = after_transfer

                    aave_to = a_record.aave_to
                    after_receive = address_token_block_balance_dic[aave_to][reserve.a_token_address][
                        a_record.block_number
                    ]
                    res_d[aave_to][reserve.asset].address = aave_to
                    res_d[aave_to][reserve.asset].asset = reserve.asset
                    res_d[aave_to][reserve.asset].block_number = a_record.block_number
                    res_d[aave_to][reserve.asset].block_timestamp = a_record.block_timestamp
                    res_d[aave_to][reserve.asset].supply_amount = after_receive
                else:
                    reserve = self.vary_debt_reserve_dic.get(a_record.a_token)
                    if reserve:
                        aave_from = a_record.aave_from
                        after_transfer = address_token_block_balance_dic[aave_from][
                            reserve.variable_debt_token_address
                        ][a_record.block_number]
                        aave_to = a_record.aave_to
                        after_receive = address_token_block_balance_dic[aave_to][reserve.variable_debt_token_address][
                            a_record.block_number
                        ]
                    else:
                        reserve = self.stable_debt_reserve_dic[a_record.a_record.a_token]
                        aave_from = a_record.aave_from
                        after_transfer = address_token_block_balance_dic[aave_from][reserve.stable_debt_token_address][
                            a_record.block_number
                        ]
                        aave_to = a_record.aave_to
                        after_receive = address_token_block_balance_dic[aave_to][reserve.stable_debt_token_address][
                            a_record.block_number
                        ]

                    res_d[aave_from][reserve.asset].address = aave_from
                    res_d[aave_from][reserve.asset].asset = reserve.asset
                    res_d[aave_from][reserve.asset].block_number = a_record.block_number
                    res_d[aave_from][reserve.asset].block_timestamp = a_record.block_timestamp
                    res_d[aave_from][reserve.asset].borrow_amount = after_transfer

                    res_d[aave_to][reserve.asset].address = aave_to
                    res_d[aave_to][reserve.asset].asset = reserve.asset
                    res_d[aave_to][reserve.asset].block_number = a_record.block_number
                    res_d[aave_to][reserve.asset].block_timestamp = a_record.block_timestamp
                    res_d[aave_to][reserve.asset].borrow_amount = after_receive

            elif a_record.type() == AaveV2RepayD.type() or a_record.type() == AaveV2BorrowD.type():
                address = a_record.aave_user
                reserve = self.reserve_dic[a_record.reserve]
                block_number = a_record.block_number

                vary_token = reserve.variable_debt_token_address
                vary_debt = 0
                if address in address_token_block_balance_dic:
                    if vary_token in address_token_block_balance_dic[address]:
                        vary_debt = address_token_block_balance_dic[address][vary_token][block_number]
                stable_token = reserve.stable_debt_token_address
                stable_debt = 0
                if address in address_token_block_balance_dic:
                    if stable_token in address_token_block_balance_dic[address]:
                        stable_debt = address_token_block_balance_dic[address][stable_token][block_number]

                res_d[address][reserve.asset].asset = reserve.asset
                res_d[address][reserve.asset].address = address
                res_d[address][reserve.asset].borrow_amount = stable_debt + vary_debt
                res_d[address][reserve.asset].block_number = a_record.block_number
                res_d[address][reserve.asset].block_timestamp = a_record.block_timestamp
            elif a_record.type() == AaveV2LiquidationCallD.type():
                address = a_record.aave_user
                block_number = a_record.block_number

                debt_asset = a_record.debt_asset
                debt_reserve = self.reserve_dic[debt_asset]
                vary_token = debt_reserve.variable_debt_token_address
                vary_debt = 0
                if address in address_token_block_balance_dic:
                    if vary_token in address_token_block_balance_dic[address]:
                        vary_debt = address_token_block_balance_dic[address][vary_token][block_number]
                stable_token = debt_reserve.stable_debt_token_address
                stable_debt = 0
                if address in address_token_block_balance_dic:
                    if stable_token in address_token_block_balance_dic[address]:
                        stable_debt = address_token_block_balance_dic[address][stable_token][block_number]
                a_record.debt_after_liquidation = vary_debt + stable_debt

                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.reserve_dic[collateral_asset]

                a_record.collateral_after_liquidation = address_token_block_balance_dic[address][
                    collateral_reserve.a_token_address
                ][block_number]

                res_d[address][collateral_asset].asset = collateral_asset
                res_d[address][collateral_asset].address = address
                res_d[address][collateral_asset].supply_amount = a_record.collateral_after_liquidation
                res_d[address][collateral_asset].block_number = a_record.block_number
                res_d[address][collateral_asset].block_timestamp = a_record.block_timestamp

                res_d[address][debt_asset].asset = debt_asset
                res_d[address][debt_asset].address = address
                res_d[address][debt_asset].borrow_amount = a_record.debt_after_liquidation
                res_d[address][debt_asset].block_number = a_record.block_number
                res_d[address][debt_asset].block_timestamp = a_record.block_timestamp

                # record last liquidation time and amount
                self._collect_item(
                    AaveV2LiquidationAddressCurrentD.type(),
                    AaveV2LiquidationAddressCurrentD(
                        address=address,
                        asset=collateral_asset,
                        last_liquidation_time=a_record.block_timestamp,
                        last_total_value_of_liquidation=a_record.liquidated_collateral_amount,
                        block_number=a_record.block_number,
                    ),
                )
        return res_d

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

                if processed_data.type() == AaveV2ReserveD.type():
                    # update reserve
                    self.reserve_dic[processed_data.asset] = processed_data
                    self.a_token_reserve_dic[processed_data.a_token_address] = processed_data
                elif processed_data.type() == AaveV2ReserveDataD.type():
                    self._collect_item(
                        AaveV2ReserveDataCurrentD.type(),
                        AaveV2ReserveDataCurrentD(
                            asset=processed_data.asset,
                            block_number=processed_data.block_number,
                            block_timestamp=processed_data.block_timestamp,
                            liquidity_rate=processed_data.liquidity_rate,
                            stable_borrow_rate=processed_data.stable_borrow_rate,
                            variable_borrow_rate=processed_data.variable_borrow_rate,
                            liquidity_index=processed_data.liquidity_index,
                            variable_borrow_index=processed_data.variable_borrow_index,
                        ),
                    )
                self._collect_item(processed_data.type(), processed_data)
                aave_records.append(processed_data)
            except Exception as e:
                logger.error(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}: {str(e)}")
                raise FastShutdownError(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}")

        address_token_block_balance_dic = self._enrich_records(aave_records)
        res_d = self.update_address_current(aave_records, address_token_block_balance_dic)
        address_currents = []
        for address, outer_dic in res_d.items():
            for reserve, kad in outer_dic.items():
                address_currents.append(kad)
        self._collect_items(AaveV2AddressCurrentD.type(), address_currents)
        merge_dataclasses(self, AaveV2ReserveDataD, ["asset"])
        merge_dataclasses(self, AaveV2ReserveDataCurrentD, ["asset"])
        merge_dataclasses(self, AaveV2LiquidationAddressCurrentD, ["address", "asset"])

        logger.info("This batch of data have processed")

    def _enrich_records(self, aave_records):
        eth_call_lis = []
        for a_record in aave_records:
            if a_record.type() == AaveV2DepositD.type():
                reserve = self.reserve_dic[a_record.reserve]
                eth_call_lis.append(
                    Call(
                        target=reserve.a_token_address,
                        function_abi=SCALED_BALANCE_OF_FUNCTION,
                        parameters=[a_record.aave_user],
                        block_number=a_record.block_number,
                    )
                )
            elif a_record.type() == AaveV2WithdrawD.type():
                reserve = self.reserve_dic[a_record.reserve]
                eth_call_lis.append(
                    Call(
                        target=reserve.a_token_address,
                        function_abi=SCALED_BALANCE_OF_FUNCTION,
                        parameters=[a_record.aave_user],
                        block_number=a_record.block_number,
                    )
                )
            elif a_record.type() == AaveV2TransferD.type():
                if a_record.a_token in self.a_token_reserve_dic or a_record.a_token in self.vary_debt_reserve_dic:
                    a_token_address = a_record.a_token
                    eth_call_lis.append(
                        Call(
                            target=a_token_address,
                            function_abi=SCALED_BALANCE_OF_FUNCTION,
                            parameters=[a_record.aave_from],
                            block_number=a_record.block_number,
                        )
                    )
                    eth_call_lis.append(
                        Call(
                            target=a_token_address,
                            function_abi=SCALED_BALANCE_OF_FUNCTION,
                            parameters=[a_record.aave_to],
                            block_number=a_record.block_number,
                        )
                    )
                elif a_record.a_token in self.stable_debt_reserve_dic:
                    a_token_address = a_record.a_token
                    eth_call_lis.append(
                        Call(
                            target=a_token_address,
                            function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                            parameters=[a_record.aave_from],
                            block_number=a_record.block_number,
                        )
                    )
                    eth_call_lis.append(
                        Call(
                            target=a_token_address,
                            function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                            parameters=[a_record.aave_to],
                            block_number=a_record.block_number,
                        )
                    )
            elif a_record.type() == AaveV2RepayD.type() or a_record.type() == AaveV2BorrowD.type():
                reserve = self.reserve_dic[a_record.reserve]
                eth_call_lis.append(
                    Call(
                        target=reserve.stable_debt_token_address,
                        function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                        parameters=[a_record.aave_user],
                        block_number=a_record.block_number,
                    )
                )
                eth_call_lis.append(
                    Call(
                        target=reserve.variable_debt_token_address,
                        function_abi=SCALED_BALANCE_OF_FUNCTION,
                        parameters=[a_record.aave_user],
                        block_number=a_record.block_number,
                    )
                )

            elif a_record.type() == AaveV2LiquidationCallD.type():
                aave_user = a_record.aave_user
                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.reserve_dic[collateral_asset]
                eth_call_lis.append(
                    Call(
                        target=collateral_reserve.a_token_address,
                        function_abi=SCALED_BALANCE_OF_FUNCTION,
                        parameters=[aave_user],
                        block_number=a_record.block_number,
                    )
                )
                debt_asset = a_record.debt_asset
                debt_reserve = self.reserve_dic[debt_asset]

                eth_call_lis.append(
                    Call(
                        target=debt_reserve.stable_debt_token_address,
                        function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                        parameters=[aave_user],
                        block_number=a_record.block_number,
                    )
                )
                eth_call_lis.append(
                    Call(
                        target=debt_reserve.variable_debt_token_address,
                        function_abi=SCALED_BALANCE_OF_FUNCTION,
                        parameters=[aave_user],
                        block_number=a_record.block_number,
                    )
                )

        enriched_eth_call_lis = self.multicall_helper.execute_calls(eth_call_lis)

        address_token_block_balance_dic = {}

        unique_set = set()
        for cl in enriched_eth_call_lis:
            k = (
                cl.target.lower(),
                cl.block_number,
                cl.function_abi.get_name(),
                ",".join(cl.parameters if cl.parameters else ""),
            )
            if k in unique_set:
                continue
            unique_set.add(k)
            self._collect_item(
                AaveV2CallRecordsD.type(),
                AaveV2CallRecordsD(
                    target=cl.target.lower(),
                    params=",".join(cl.parameters) if cl.parameters else "",
                    function=cl.function_abi.get_name(),
                    block_number=cl.block_number,
                    result=str(cl.returns),
                ),
            )
            token = cl.target.lower()
            block_number = cl.block_number

            address = cl.parameters[0]
            if address not in address_token_block_balance_dic:
                address_token_block_balance_dic[address] = dict()
            if token not in address_token_block_balance_dic[address]:
                address_token_block_balance_dic[address][token] = dict()
            if cl.returns is None:
                address_token_block_balance_dic[address][token][block_number] = 0
            else:
                address_token_block_balance_dic[address][token][block_number] = cl.returns["balance"]
        return address_token_block_balance_dic
