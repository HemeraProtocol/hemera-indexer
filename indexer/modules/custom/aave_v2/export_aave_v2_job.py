import logging
from collections import defaultdict
from typing import Any, cast

from sqlalchemy import func
from web3.types import ABIEvent

from common.utils.abi_code_utils import AbiReader, Event
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.aave_v2.aave_v2_processors import AaveV2Events
from indexer.modules.custom.aave_v2.domains.aave_v2_domain import (
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
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportAaveV2Job(FilterTransactionDataJob):
    """This job extract aave_v2 related infos
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

        self.contract_addresses = {"POOL": self.job_conf["POOL"], "POOL_CONFIGURE": self.job_conf["POOL_CONFIGURE"]}

        self.address_set = set(self.contract_addresses.values())

        # event_name -> Event
        self.events = {}
        # sig -> processor
        self._event_processors = {}
        self._initialize_events_and_processors()

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
        res = []
        for log in logs:
            if not self.is_aave_v2_address(log.address):
                continue
            try:
                processor = self._event_processors.get(log.topic0)
                if processor is None:
                    continue
                processed_data = processor.process(log)
                res.append(processed_data)

            except Exception as e:
                logger.error(f"Error processing log {log.log_index} " f"in tx {log.transaction_hash}: {str(e)}")
                raise FastShutdownError("Error processing log {log.log_index} " f"in tx {log.transaction_hash}")

        for it in res:
            self._collect_item(it.type(), it)
        liquidation_lis = []
        batch_result_dic = self.calculate_batch_result(res, liquidation_lis)
        liquidation_lis = self.merge_liquidation_lis(liquidation_lis)
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

    def merge_liquidation_lis(self, liquidation_lis):
        # keep the newest one
        liquidation_lis.sort(key=lambda x: x.last_liquidation_time, reverse=False)
        lis = []
        unique_k_set = set()
        for li in liquidation_lis:
            k = (li.address, li.asset)
            if k not in unique_k_set:
                unique_k_set.add(k)
                lis.append(li)
        return lis

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
                res_d[user][reserve].borrow_amount += action.amount
                res_d[user][reserve].block_number = action.block_number
                res_d[user][reserve].block_timestamp = action.block_timestamp
            elif event_name == AaveV2Events.REPAY.value.name:
                reserve = action.reserve
                user = action.aave_user
                res_d[user][reserve].asset = reserve
                res_d[user][reserve].address = user
                res_d[user][reserve].borrow_amount -= action.amount
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
