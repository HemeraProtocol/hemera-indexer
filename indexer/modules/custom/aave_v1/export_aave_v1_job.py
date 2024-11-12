import logging
from collections import defaultdict

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
    ReserveUpdatedProcessor,
    WithdrawProcessor,
)
from indexer.modules.custom.aave_v1.abi.abi import (
    BORROW_EVENT,
    DEPOSIT_EVENT,
    FLUSH_LOAN_EVENT,
    LIQUIDATION_CALL_EVENT,
    PRINCIPAL_BALANCE_OF_FUNCTION,
    REDEEM_EVENT,
    REPAY_EVENT,
    RESERVE_INITIALIZED_EVENT,
    RESERVE_UPDATED_EVENT,
    USER_BORROW_BALANCE_FUNCTION,
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
    AaveV1ReserveDataCurrentD,
    AaveV1ReserveDataD,
    AaveV1WithdrawD,
    aave_v1_address_current_factory,
)
from indexer.modules.custom.aave_v1.models.aave_v1_reserve_current import AaveV1ReserveCurrent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)

GET_USRE_BALANCE = "getUserBorrowBalances(address,address)(uint256,uint256,uint256)"


class ExportAaveV1Job(FilterTransactionDataJob):
    """This job extract aave_v1 related infos"""

    dependency_types = [Log]
    output_types = [
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
        AaveV1ReserveDataD,
        AaveV1ReserveDataCurrentD,
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
        self.multicall_helper = MultiCallHelper(self._web3, kwargs)
        self.address_set = set(self.contract_addresses.values())

        # sig -> processor
        self._event_processors = {}
        self._initialize_events_and_processors()

        # init relative tokens
        self.reserve_dic = {}
        self._read_reserve()

    def _read_reserve(self):

        with self.db_service.get_service_session() as session:
            result = session.query(AaveV1ReserveCurrent).all()
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
            ReserveInitProcessor(RESERVE_INITIALIZED_EVENT, AaveV1ReserveD, multicall_helper=self.multicall_helper),
            DepositProcessor(DEPOSIT_EVENT, AaveV1DepositD),
            WithdrawProcessor(REDEEM_EVENT, AaveV1WithdrawD),
            BorrowProcessor(BORROW_EVENT, AaveV1BorrowD),
            RepayProcessor(REPAY_EVENT, AaveV1RepayD),
            FlashLoanProcessor(FLUSH_LOAN_EVENT, AaveV1FlashLoanD),
            LiquidationCallProcessor(LIQUIDATION_CALL_EVENT, AaveV1LiquidationCallD),
            ReserveUpdatedProcessor(RESERVE_UPDATED_EVENT, AaveV1ReserveDataD),
        ]
        self._event_processors = {p.event.get_signature(): p for p in processors}

    def get_filter(self):
        topics = [p for p in self._event_processors.keys()]
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
                elif processed_data.type() == AaveV1ReserveDataD.type():
                    self._collect_item(
                        AaveV1ReserveDataCurrentD.type(),
                        AaveV1ReserveDataCurrentD(
                            asset=bytes_to_hex_str(log.asset),
                            block_number=log.block_number,
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

        address_token_block_balance_dic, address_asset_block_borrow_balance_dic = self._enrich_records(aave_records)
        liquidation_lis = []

        def nested_dict():
            return defaultdict(aave_v1_address_current_factory)

        res_d = defaultdict(nested_dict)
        # enrich repay, liquidation
        for a_record in aave_records:
            if a_record.type() == AaveV1RepayD.type() or a_record.type() == AaveV1BorrowD.type():
                address = a_record.aave_user
                reserve = a_record.reserve
                block_number = a_record.block_number

                debt = 0
                if address in address_asset_block_borrow_balance_dic:
                    if reserve in address_asset_block_borrow_balance_dic[address]:
                        debt = address_asset_block_borrow_balance_dic[address][reserve][block_number]

                res_d[address][reserve].asset = reserve
                res_d[address][reserve].address = address
                res_d[address][reserve].borrow_amount = debt
                res_d[address][reserve].block_number = a_record.block_number
                res_d[address][reserve].block_timestamp = a_record.block_timestamp
            elif a_record.type() == AaveV1DepositD.type() or a_record.type() == AaveV1WithdrawD.type():
                reserve = self.reserve_dic[a_record.reserve]
                address = a_record.aave_user
                after = address_token_block_balance_dic[address][reserve.a_token_address][a_record.block_number]

                res_d[address][reserve.asset].address = a_record.aave_user
                res_d[address][reserve.asset].asset = reserve.asset
                res_d[address][reserve.asset].block_number = a_record.block_number
                res_d[address][reserve.asset].block_timestamp = a_record.block_timestamp
                res_d[address][reserve.asset].supply_amount = after

            elif a_record.type() == AaveV1LiquidationCallD.type():
                address = a_record.aave_user
                block_number = a_record.block_number

                debt_asset = a_record.debt_asset
                debt = 0
                if address in address_asset_block_borrow_balance_dic:
                    if debt_asset in address_asset_block_borrow_balance_dic[address]:
                        debt = address_asset_block_borrow_balance_dic[address][debt_asset][block_number]

                a_record.debt_after_liquidation = debt

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
                    AaveV1LiquidationAddressCurrentD.type(),
                    AaveV1LiquidationAddressCurrentD(
                        address=address,
                        asset=collateral_asset,
                        last_liquidation_time=a_record.block_timestamp,
                        last_total_value_of_liquidation=a_record.liquidated_collateral_amount,
                        block_number=a_record.block_number,
                    ),
                )
        address_currents = []
        for address, outer_dic in res_d.items():
            for reserve, kad in outer_dic.items():
                address_currents.append(kad)
        self._collect_items(AaveV1AddressCurrentD.type(), address_currents)
        self._merge_dataclasses(AaveV1ReserveDataD, ["asset"])
        self._merge_dataclasses(AaveV1ReserveDataCurrentD, ["asset"])
        self._merge_dataclasses(AaveV1LiquidationAddressCurrentD, ["address", "asset"])

        logger.info("This aavev1 batch of data have processed")

    def _merge_dataclasses(self, data_class, attributes):
        """sort dataclass by block_number, then keep the newest data"""
        if data_class.type() not in self._data_buff:
            return
        tmps = self._data_buff.pop(data_class.type())
        tmps.sort(key=lambda x: x.block_number, reverse=True)
        lis = []
        unique_k_set = set()
        for li in tmps:
            k = tuple([getattr(li, at) for at in attributes])
            if k not in unique_k_set:
                unique_k_set.add(k)
                lis.append(li)
        if len(lis) > 0:
            self._collect_items(data_class.type(), lis)

    def _enrich_records(self, aave_records):
        eth_call_lis = []
        for a_record in aave_records:
            if a_record.type() == AaveV1WithdrawD.type() or a_record.type() == AaveV1DepositD.type():
                reserve = self.reserve_dic[a_record.reserve]
                user = a_record.aave_user
                eth_call_lis.append(
                    Call(
                        reserve.a_token_address,
                        function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                        parameters=[user],
                        block_number=a_record.block_number,
                    )
                )
            elif a_record.type() == AaveV1BorrowD.type() or a_record.type() == AaveV1RepayD.type():
                user = a_record.aave_user
                reserve = a_record.reserve
                eth_call_lis.append(
                    Call(
                        self.contract_addresses["POOL_V1_CORE"],
                        function_abi=USER_BORROW_BALANCE_FUNCTION,
                        block_number=a_record.block_number,
                        parameters=[reserve, user],
                    )
                )
            elif a_record.type() == AaveV1LiquidationCallD.type():
                aave_user = a_record.aave_user
                collateral_asset = a_record.collateral_asset
                collateral_reserve = self.reserve_dic[collateral_asset]
                eth_call_lis.append(
                    Call(
                        target=collateral_reserve.a_token_address,
                        function_abi=PRINCIPAL_BALANCE_OF_FUNCTION,
                        parameters=[aave_user],
                        block_number=a_record.block_number,
                    )
                )
                eth_call_lis.append(
                    Call(
                        target=self.contract_addresses["POOL_V1_CORE"],
                        function_abi=USER_BORROW_BALANCE_FUNCTION,
                        parameters=[collateral_reserve, aave_user],
                        block_number=a_record.block_number,
                    )
                )

        enriched_eth_call_lis = self.multicall_helper.execute_calls(eth_call_lis)
        address_token_block_balance_dic = {}
        address_asset_block_borrow_balance_dic = {}

        unique_set = set()
        for cl in enriched_eth_call_lis:
            k = (cl.target.lower(), cl.block_number, cl.function_abi.get_name(), ",".join(cl.parameters))
            if k in unique_set:
                continue
            unique_set.add(k)
            self._collect_item(
                AaveV1CallRecordsD.type(),
                AaveV1CallRecordsD(
                    target=cl.target.lower(),
                    params=",".join(cl.parameters),
                    function=cl.function_abi.get_name(),
                    block_number=cl.block_number,
                    result=str(cl.returns),
                ),
            )
            token = cl.target.lower()
            block_number = cl.block_number
            if cl.function_abi.get_name().startswith("getUserBorrowBalances"):
                address = cl.parameters[1]
                asset = cl.parameters[0]
                if address not in address_asset_block_borrow_balance_dic:
                    address_asset_block_borrow_balance_dic[address] = dict()
                if asset not in address_asset_block_borrow_balance_dic[address]:
                    address_asset_block_borrow_balance_dic[address][asset] = dict()
                address_asset_block_borrow_balance_dic[address][asset][block_number] = cl.returns["principal_balance"]
            else:
                address = cl.parameters[0]
                if address not in address_token_block_balance_dic:
                    address_token_block_balance_dic[address] = dict()
                if token not in address_token_block_balance_dic[address]:
                    address_token_block_balance_dic[address][token] = dict()
                address_token_block_balance_dic[address][token][block_number] = cl.returns["balance"]
        return address_token_block_balance_dic, address_asset_block_borrow_balance_dic
