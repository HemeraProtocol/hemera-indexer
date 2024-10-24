import logging
from collections import defaultdict
from dataclasses import fields
from itertools import groupby
from operator import attrgetter
from typing import Any, cast

from sqlalchemy import func
from web3.types import ABIEvent

from common.utils.abi_code_utils import AbiReader, Event
from common.utils.format_utils import bytes_to_hex_str
from common.utils.web3_utils import extract_eth_address
from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.aave_v2.domains.aave_v2_domain import (
    AaveV2AddressCurrentD,
    AaveV2BorrowD,
    AaveV2DepositD,
    AaveV2FlashLoanD,
    AaveV2LendingPoolReserveFactorCurrent,
    AaveV2LendingPoolReserveFactorRecord,
    AaveV2LiquidationAddressCurrentD,
    AaveV2LiquidationCallD,
    AaveV2RepayD,
    AaveV2ReserveD,
    AaveV2WithdrawD,
    aave_v2_address_current_factory,
)
from indexer.modules.custom.aave_v2.models.aave_v2_address_current import AaveV2AddressCurrent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportAaveV2Job(FilterTransactionDataJob):
    """This job is for extract below infos:
    Add collateral, borrow asset records
    Amount of collateral (token_address + amount) added for each address
    Amount of asset (token_address + amount) borrowed for each address
    Liquidation record
    Total value of liquidation for each wallet
    """

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
    ]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")

        self.job_conf = self.user_defined_config
        self.abi_reader = AbiReader(__file__)

        self.lending_pool_address = self.job_conf["POOL"]
        self.lending_pool_configure_address = self.job_conf["POOL_CONFIGURE"]
        self.address_set = {self.lending_pool_address, self.lending_pool_configure_address}

        self.reserve_init_event = Event(
            cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_configure_address, "ReserveInitialized"))
        )

        self.deposit_event = Event(cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "Deposit")))
        self.withdraw_event = Event(
            cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "Withdraw"))
        )
        self.borrow_event = Event(cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "Borrow")))
        self.repay_event = Event(cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "Repay")))
        self.flash_loan_event = Event(
            cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "FlashLoan"))
        )
        self.liquidation_call_event = Event(
            cast(ABIEvent, self.abi_reader.get_event_abi(self.lending_pool_address, "LiquidationCall"))
        )

    def get_filter(self):
        topics = [
            self.reserve_init_event.get_signature(),
            self.deposit_event.get_signature(),
            self.withdraw_event.get_signature(),
            self.borrow_event.get_signature(),
            self.repay_event.get_signature(),
            self.flash_loan_event.get_signature(),
            self.liquidation_call_event.get_signature(),
        ]
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[self.lending_pool_address, self.lending_pool_configure_address], topics=topics
                ),
            ]
        )

    def is_aave_v2_address(self, address):
        return address in self.address_set

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        res = []
        for log in logs:
            if not self.is_aave_v2_address(log.address):
                continue
            current_topic0 = log.topic0
            if current_topic0 == self.reserve_init_event.get_signature():
                # 0x3a0ca721fc364424566385a1aa271ed508cc2c0949c2272575fb3013a163a45f
                dl = self.reserve_init_event.decode_log(log)
                tmp: AaveV2ReserveD = AaveV2ReserveD(
                    asset=common_utils.parse_hex_to_address(log.topic1),
                    a_token_address=common_utils.parse_hex_to_address(log.topic2),
                    stable_debt_token_address=dl.get("stableDebtToken"),
                    variable_debt_token_address=dl.get("variableDebtToken"),
                    interest_rate_strategy_address=dl.get("interestRateStrategyAddress"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                )
                res.append(tmp)
            elif current_topic0 == self.deposit_event.get_signature():
                # 0xde6857219544bb5b7746f48ed30be6386fefc61b2f864cacf559893bf50fd951
                dl = self.deposit_event.decode_log(log)
                tmp: AaveV2DepositD = AaveV2DepositD(
                    reserve=extract_eth_address(log.topic1),
                    # who receive atoken
                    on_behalf_of=extract_eth_address(log.topic2),
                    referral=log.topic3,
                    # who send asset
                    aave_user=dl.get("user"),
                    amount=dl.get("amount"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.deposit_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            elif current_topic0 == self.withdraw_event.get_signature():
                # 0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7
                dl = self.withdraw_event.decode_log(log)
                tmp: AaveV2WithdrawD = AaveV2WithdrawD(
                    reserve=extract_eth_address(log.topic1),
                    aave_user=extract_eth_address(log.topic2),
                    amount=dl.get("amount"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.withdraw_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            elif current_topic0 == self.borrow_event.get_signature():
                # 0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0
                dl = self.borrow_event.decode_log(log)
                tmp: AaveV2BorrowD = AaveV2BorrowD(
                    reserve=extract_eth_address(log.topic1),
                    # The address that will be getting the debt
                    on_behalf_of=extract_eth_address(log.topic2),
                    referral=log.topic3,
                    #  The address of the user initiating the borrow(), receiving the funds on borrow() or just initiator of the transaction on flashLoan()
                    aave_user=dl.get("user"),
                    amount=dl.get("amount"),
                    # The rate mode: 1 for Stable, 2 for Variable
                    borrow_rate_mode=dl.get("interestRateMode"),
                    borrow_rate=dl.get("borrowRate"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.borrow_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            elif current_topic0 == self.repay_event.get_signature():
                # 0xa534c8dbe71f871f9f3530e97a74601fea17b426cae02e1c5aee42c96c784051
                dl = self.repay_event.decode_log(log)
                tmp: AaveV2RepayD = AaveV2RepayD(
                    reserve=extract_eth_address(log.topic1),
                    # The beneficiary of the repayment, getting his debt reduced
                    aave_user=extract_eth_address(log.topic2),
                    # The address of the user initiating the repay(), providing the funds
                    repayer=extract_eth_address(log.topic3),
                    amount=dl.get("amount"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.repay_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            elif current_topic0 == self.flash_loan_event.get_signature():
                # 0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac
                dl = self.flash_loan_event.decode_log(log)
                tmp: AaveV2FlashLoanD = AaveV2FlashLoanD(
                    target=extract_eth_address(log.topic1),
                    # The beneficiary of the repayment, getting his debt reduced
                    aave_user=extract_eth_address(log.topic2),
                    # The address of the user initiating the repay(), providing the funds
                    reserve=extract_eth_address(log.topic3),
                    amount=dl.get("amount"),
                    premium=dl.get("premium"),
                    referral=dl.get("referralCode"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.flash_loan_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            elif current_topic0 == self.liquidation_call_event.get_signature():
                # 0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286
                dl = self.liquidation_call_event.decode_log(log)
                tmp: AaveV2LiquidationCallD = AaveV2LiquidationCallD(
                    collateral_asset=extract_eth_address(log.topic1),
                    debt_asset=extract_eth_address(log.topic2),
                    aave_user=extract_eth_address(log.topic3),
                    debt_to_cover=dl.get("debtToCover"),
                    liquidated_collateral_amount=dl.get("liquidatedCollateralAmount"),
                    liquidator=dl.get("liquidator"),
                    receive_atoken=dl.get("receiveAToken"),
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    event_name=self.liquidation_call_event.get_name(),
                    topic0=log.topic0,
                )
                res.append(tmp)
            # elif current_topic0 == self._change_factor_topic0:
            #     self._collect_item(
            #         AaveV2LendingPoolReserveFactorRecord.type(),
            #         AaveV2LendingPoolReserveFactorRecord(
            #             asset_address=common_utils.parse_hex_to_address(log.topic1),
            #             factor=common_utils.parse_hex_to_int256(log.data),
            #             block_number=log.block_number,
            #             block_timestamp=log.block_timestamp,
            #         ),
            #     )
        for it in res:
            self._collect_item(it.type(), it)
        liquidation_lis = []
        batch_result_dic = self.calculate_batch_result(res, liquidation_lis)
        self._collect_items(AaveV2LiquidationAddressCurrentD.type(), liquidation_lis)
        exists_dic = self.get_existing_address_current(list(batch_result_dic.keys()))
        for address, outer_dic in batch_result_dic.items():
            for reserve, kad in outer_dic.items():
                if address in exists_dic and reserve in exists_dic[address]:
                    exists_aad = exists_dic[address][reserve]
                    exists_aad.supply_amount += kad.supply_amount
                    exists_aad.borrow_amount += kad.borrow_amount
                    self._collect_item(kad.type(), exists_aad)
                else:
                    self._collect_item(kad.type(), kad)
        logger.info("This batch of data have processed")
        # self._process_current_pool_data()

    def get_existing_address_current(self, addresses):
        if not self.db_service:
            return {}

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
                block_number=rr.block_number,
                block_timestamp=int(rr.block_timestamp.timestamp()),
            )
            if item.address not in res:
                res[item.address] = {}
            res[item.address][item.asset] = item
        return res

    def calculate_batch_result(self, aave_records, liquidation_lis) -> Any:
        def nested_dict():
            return defaultdict(aave_v2_address_current_factory)

        res_d = defaultdict(nested_dict)
        for action in aave_records:
            if not hasattr(action, "event_name"):
                continue
            event_name = action.event_name

            if event_name == self.deposit_event.get_name():
                user = action.on_behalf_of
                reserve = action.reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].supply_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == self.borrow_event.get_name():
                reserve = action.reserve
                user = action.on_behalf_of
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].borrow_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == self.repay_event.get_name():
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].borrow_amount -= action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == self.withdraw_event.get_name():
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].address = user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].supply_amount -= action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == self.liquidation_call_event.get_name():
                collateral_asset = action.collateral_asset
                debt_asset = action.debt_asset
                user = action.aave_user
                res_d[user][collateral_asset].asset = collateral_asset
                res_d[user][collateral_asset].address = user
                res_d[user][collateral_asset].supply_amount = 0
                res_d[user][collateral_asset].block_number = action.block_number
                res_d[user][collateral_asset].block_timestamp = action.block_timestamp

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

    def _process_current_pool_data(self):
        records = self._data_buff[AaveV2LendingPoolReserveFactorRecord.type()]
        self._data_buff[AaveV2LendingPoolReserveFactorRecord.type()] = []
        unique_records = {}
        for record in records:
            key = (record.asset_address, record.block_number)
            unique_records[key] = record

        for price in unique_records.values():
            self._collect_item(AaveV2LendingPoolReserveFactorRecord.type(), price)

        sorted_records = sorted(unique_records.values(), key=lambda x: (x.asset_address, x.block_number))
        current_records = [
            max(group, key=attrgetter("block_number"))
            for _, group in groupby(sorted_records, key=attrgetter("asset_address"))
        ]
        for data in current_records:
            self._collect_item(AaveV2LendingPoolReserveFactorCurrent.type(), self.create_current_status(data))

    @staticmethod
    def create_current_status(detail: AaveV2LendingPoolReserveFactorRecord) -> AaveV2LendingPoolReserveFactorCurrent:
        return AaveV2LendingPoolReserveFactorCurrent(
            **{field.name: getattr(detail, field.name) for field in fields(AaveV2LendingPoolReserveFactorRecord)}
        )
