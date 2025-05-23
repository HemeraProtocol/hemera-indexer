import logging

import orjson

# Utility
from hemera.common.utils.abi_code_utils import decode_data, decode_log
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes

# Dependency dataclass
from hemera.indexer.domains.log import Log

# Job
from hemera.indexer.jobs.base_job import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from hemera.indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

# Custom dataclass
from hemera_udf.init_capital.abi import (
    INIT_BORROW_EVENT,
    INIT_COLLATERALIZE_EVENT,
    INIT_CREATE_POSITION_EVENT,
    INIT_DECOLLATERALIZE_EVENT,
    INIT_LIQUIDATE_EVENT,
    INIT_POOL_TOTAL_ASSETS_FUNCTION,
    INIT_POOL_TOTAL_DEBT_FUNCTION,
    INIT_POOL_TOTAL_DEBT_SHARES_FUNCTION,
    INIT_POOL_TOTAL_SUPPLY_FUNCTION,
    INIT_REPAY_EVENT,
)
from hemera_udf.init_capital.domains import (
    InitCapitalPoolHistoryDomain,
    InitCapitalPoolUpdateDomain,
    InitCapitalPositionCreateDomain,
    InitCapitalPositionHistoryDomain,
    InitCapitalPositionUpdateDomain,
    InitCapitalRecordDomain,
)
from hemera_udf.init_capital.models.init_capital_models import InitCapitalPoolCurrent, InitCapitalPositionCurrent

logger = logging.getLogger(__name__)

INIT_CORE = "0x972BcB0284cca0152527c4f70f8F689852bCAFc5"

"""
https://docs.init.capital/
# MONEY_MARKET_HOOK = "0xf82cbcab75c1138a8f1f20179613e7c0c8337346"
# MARGIN_TRADING_HOOK = "0x7fa704E73262e5A9f48382087F69C6Aba0408eAA"
# POS_MANAGER = "0x0e7401707CD08c03CDb53DAEF3295DDFb68BBa92"
"""


class InitCapitalJob(FilterTransactionDataJob):
    # Declare existing dataclass you may need for your job
    # The indexer will automatically run other jobs and prepare the dataclass
    dependency_types = [Log]

    # This is to declare output dataclass your job outputs
    # This is helpful if you write other job which depends on these dataclasses
    output_types = [
        InitCapitalPositionCreateDomain,
        InitCapitalPositionHistoryDomain,
        InitCapitalPositionUpdateDomain,
        InitCapitalRecordDomain,
        InitCapitalPoolUpdateDomain,
        InitCapitalPoolHistoryDomain,
    ]

    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")
        self._pool_token_map = self.get_pool_token_maps()
        self._init_core = self.user_defined_config.get("core_address")

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=[self._init_core],
                topics=[
                    INIT_DECOLLATERALIZE_EVENT.get_signature(),
                    INIT_COLLATERALIZE_EVENT.get_signature(),
                    INIT_BORROW_EVENT.get_signature(),
                    INIT_REPAY_EVENT.get_signature(),
                    INIT_CREATE_POSITION_EVENT.get_signature(),
                    INIT_LIQUIDATE_EVENT.get_signature(),
                ],
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        # This is how you get your dependency dataclass indexer prepared for you
        # Note that filter will apply
        logs = self._data_buff[Log.type()]

        # Core logic of UDF
        # 1. Create new position (if any)
        new_positions = []
        existing_position_ids = []
        for log in logs:
            if log.topic0 == INIT_CREATE_POSITION_EVENT.get_signature():
                decoded_data = decode_log(INIT_CREATE_POSITION_EVENT.get_abi(), log)
                new_position = InitCapitalPositionCreateDomain(
                    position_id=decoded_data["posId"],
                    owner_address=decoded_data["owner"],
                    viewer_address=decoded_data["viewer"],
                    mode=decoded_data["mode"],
                    created_block_number=log.block_number,
                    created_block_timestamp=log.block_timestamp,
                    created_transaction_hash=log.transaction_hash,
                    created_log_index=log.log_index,
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                )
                new_positions.append(new_position)
            elif log.topic0 in [
                INIT_DECOLLATERALIZE_EVENT.get_signature(),
                INIT_COLLATERALIZE_EVENT.get_signature(),
                INIT_LIQUIDATE_EVENT.get_signature(),
            ]:
                existing_position_ids.append(decode_data("uint256", hex_str_to_bytes(log.topic1))[0])
            elif log.topic0 in [
                INIT_BORROW_EVENT.get_signature(),
                INIT_REPAY_EVENT.get_signature(),
            ]:
                existing_position_ids.append(decode_data("uint256", hex_str_to_bytes(log.topic2))[0])

        existing_position_ids = list(set(existing_position_ids))

        # 2. Fetch existing postition
        existing_positions = self.get_existing_positions(existing_position_ids)
        new_position_map = {}
        existing_position_map = {p.position_id: p for p in existing_positions}

        for position in new_positions:
            new_position_map[position.position_id] = position
            existing_position_map[position.position_id] = InitCapitalPositionUpdateDomain(
                position_id=position.position_id,
                owner_address=position.owner_address,
                viewer_address=position.viewer_address,
                mode=position.mode,
                collaterals={},
                borrows={},
                block_number=position.block_number,
                block_timestamp=position.block_timestamp,
            )

        # 3. Group logs by blocks and and position ids
        grouped_logs = {}
        for log in logs:
            if log.topic0 == INIT_CREATE_POSITION_EVENT.get_signature():
                continue
            if log.block_number not in grouped_logs:
                grouped_logs[log.block_number] = {}

            position_id = None
            if log.topic0 in [
                INIT_DECOLLATERALIZE_EVENT.get_signature(),
                INIT_COLLATERALIZE_EVENT.get_signature(),
                INIT_LIQUIDATE_EVENT.get_signature(),
            ]:
                position_id = decode_data("uint256", hex_str_to_bytes(log.topic1))[0]
            elif log.topic0 in [
                INIT_BORROW_EVENT.get_signature(),
                INIT_REPAY_EVENT.get_signature(),
            ]:
                position_id = decode_data("uint256", hex_str_to_bytes(log.topic2))[0]

            if not position_id:
                continue

            if position_id not in grouped_logs[log.block_number]:
                grouped_logs[log.block_number][position_id] = []

            grouped_logs[log.block_number][position_id].append(log)

        # 4. Iterate blocks and update positions
        position_history_map = {}
        record_map = {}
        block_pool_to_update = []
        sorted_block_numbers = sorted(list(grouped_logs.keys()))
        for block_number in sorted_block_numbers:
            pools_to_update = []
            for position_id in grouped_logs[block_number]:
                existing_position = existing_position_map[position_id]

                for log in grouped_logs[block_number][position_id]:
                    if log.topic0 == INIT_COLLATERALIZE_EVENT.get_signature():
                        decoded_data = decode_log(INIT_COLLATERALIZE_EVENT.get_abi(), log)
                        record_map[(log.transaction_hash, log.log_index)] = InitCapitalRecordDomain(
                            action_type=1,
                            position_id=position_id,
                            pool_address=decoded_data["pool"],
                            token_address=self._pool_token_map[decoded_data["pool"]],
                            amount=decoded_data["amt"],
                            share=None,
                            address=existing_position.viewer_address,
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                        self.update_position_collaterals(existing_position, decoded_data["pool"], decoded_data["amt"])
                        pools_to_update.append(decoded_data["pool"])

                    elif log.topic0 == INIT_DECOLLATERALIZE_EVENT.get_signature():
                        decoded_data = decode_log(INIT_DECOLLATERALIZE_EVENT.get_abi(), log)
                        record_map[(log.transaction_hash, log.log_index)] = InitCapitalRecordDomain(
                            action_type=3,
                            position_id=position_id,
                            pool_address=decoded_data["pool"],
                            token_address=self._pool_token_map[decoded_data["pool"]],
                            amount=decoded_data["amt"],
                            share=None,
                            address=decoded_data["to"],
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                        self.update_position_collaterals(existing_position, decoded_data["pool"], -decoded_data["amt"])
                        pools_to_update.append(decoded_data["pool"])

                    elif log.topic0 == INIT_LIQUIDATE_EVENT.get_signature():
                        decoded_data = decode_log(INIT_LIQUIDATE_EVENT.get_abi(), log)
                        record_map[(log.transaction_hash, log.log_index)] = InitCapitalRecordDomain(
                            action_type=5,
                            position_id=position_id,
                            pool_address=decoded_data["poolOut"],
                            token_address=self._pool_token_map[decoded_data["poolOut"]],
                            amount=decoded_data["shares"],
                            share=None,
                            address=decoded_data["liquidator"],
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                        self.update_position_collaterals(
                            existing_position, decoded_data["poolOut"], -decoded_data["shares"]
                        )
                        pools_to_update.append(decoded_data["poolOut"])

                    elif log.topic0 == INIT_BORROW_EVENT.get_signature():
                        decoded_data = decode_log(INIT_BORROW_EVENT.get_abi(), log)
                        record_map[(log.transaction_hash, log.log_index)] = InitCapitalRecordDomain(
                            action_type=2,
                            position_id=position_id,
                            pool_address=decoded_data["pool"],
                            token_address=self._pool_token_map[decoded_data["pool"]],
                            amount=decoded_data["borrowAmt"],
                            share=decoded_data["shares"],
                            address=decoded_data["to"],
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                        self.update_position_borrows(
                            existing_position, decoded_data["pool"], decoded_data["borrowAmt"], decoded_data["shares"]
                        )
                        pools_to_update.append(decoded_data["pool"])

                    elif log.topic0 == INIT_REPAY_EVENT.get_signature():
                        decoded_data = decode_log(INIT_REPAY_EVENT.get_abi(), log)
                        record_map[(log.transaction_hash, log.log_index)] = InitCapitalRecordDomain(
                            action_type=4,
                            position_id=position_id,
                            pool_address=decoded_data["pool"],
                            token_address=self._pool_token_map[decoded_data["pool"]],
                            amount=decoded_data["amtToRepay"],
                            share=decoded_data["shares"],
                            address=decoded_data["repayer"],
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                        self.update_position_borrows(
                            existing_position,
                            decoded_data["pool"],
                            -decoded_data["amtToRepay"],
                            -decoded_data["shares"],
                        )
                        pools_to_update.append(decoded_data["pool"])

                existing_position.block_number = log.block_number
                existing_position.block_timestamp = log.block_timestamp

                position_history_map[(position_id, block_number)] = InitCapitalPositionHistoryDomain(
                    position_id=position_id,
                    owner_address=existing_position.owner_address,
                    viewer_address=existing_position.viewer_address,
                    mode=existing_position.mode,
                    collaterals=existing_position.collaterals,
                    borrows=existing_position.borrows,
                    block_number=existing_position.block_number,
                    block_timestamp=existing_position.block_timestamp,
                )
                block_pool_to_update.append(
                    [block_number, existing_position.block_timestamp, list(set(pools_to_update))]
                )

        # 5. Get pool updates
        pool_history, pool_current = self.get_pool_info_updates(block_pool_to_update)

        # This is one of the functions that convert dataclass into models and export
        # The other functions can be found in indexer/jobs/base_job.py
        self._collect_domains(list(new_position_map.values()))
        self._collect_domains(list(existing_position_map.values()))
        self._collect_domains(list(position_history_map.values()))  # InitCapitalPositionHistoryDomain
        self._collect_domains(list(record_map.values()))  # InitCapitalRecordDomain
        self._collect_domains(pool_history)  # InitCapitalPoolHistoryDomain
        self._collect_domains(pool_current)  # InitCapitalPoolUpdateDomain

    def _process(self, **kwargs):
        pass

    def get_existing_positions(self, existing_position_ids):
        if not self.db_service:
            return []
        if not existing_position_ids:
            return []
        existing_positions = []

        with self.db_service.get_service_session() as session:
            result = (
                session.query(InitCapitalPositionCurrent)
                .filter(InitCapitalPositionCurrent.position_id.in_(existing_position_ids))
                .all()
            )

        for record in result:
            existing_positions.append(
                InitCapitalPositionUpdateDomain(
                    position_id=record.position_id,
                    owner_address=bytes_to_hex_str(record.owner_address),
                    viewer_address=bytes_to_hex_str(record.viewer_address),
                    mode=record.mode,
                    collaterals=record.collaterals,
                    borrows=record.borrows,
                    block_number=record.block_number,
                    block_timestamp=record.block_timestamp,
                )
            )

        return existing_positions

    def update_position_collaterals(self, position: InitCapitalPositionUpdateDomain, pool_address, amount):
        collaterals = position.collaterals or []
        is_exist = False
        for collateral in collaterals:
            if collateral["pool_address"] == pool_address:
                collateral["amount"] += amount
                is_exist = True

        if not is_exist:
            collaterals.append(
                {
                    "pool_address": pool_address,
                    "token_address": self._pool_token_map[pool_address],
                    "amount": amount,
                }
            )

        position.collaterals = collaterals

    def update_position_borrows(self, position: InitCapitalPositionUpdateDomain, pool_address, amount, share):
        borrows = position.borrows or []
        is_exist = False
        for borrow in borrows:
            if borrow["pool_address"] == pool_address:
                borrow["amount"] += amount
                borrow["share"] += share
                is_exist = True

        if not is_exist:
            borrows.append(
                {
                    "pool_address": pool_address,
                    "token_address": self._pool_token_map[pool_address],
                    "amount": amount,
                    "share": share,
                }
            )
        position.borrows = borrows

    def get_pool_token_maps(self):
        pool_token_map = {}
        with self.db_service.get_service_session() as session:
            result = session.query(InitCapitalPoolCurrent).all()

        for record in result:
            pool_token_map[bytes_to_hex_str(record.pool_address)] = bytes_to_hex_str(record.token_address)

        return pool_token_map

    def get_pool_info_updates(self, block_pool_to_update):
        pool_info_list = []
        for block_number, block_timestamp, pool_address_list in block_pool_to_update:
            for pool_address in pool_address_list:
                for function in [
                    INIT_POOL_TOTAL_ASSETS_FUNCTION,
                    INIT_POOL_TOTAL_SUPPLY_FUNCTION,
                    INIT_POOL_TOTAL_DEBT_SHARES_FUNCTION,
                    INIT_POOL_TOTAL_DEBT_FUNCTION,
                ]:
                    params = {
                        "param_to": pool_address,
                        "param_data": function.get_signature(),
                        "param_number": block_number,
                        "request_id": str(block_number) + "-" + pool_address + "-" + function.get_signature(),
                        "block_timestamp": block_timestamp,
                    }
                    pool_info_list.append(params)

        if len(pool_info_list) <= 0:
            return [], []

        response = self._batch_web3_provider.make_request(
            params=orjson.dumps(list(generate_eth_call_json_rpc(pool_info_list)))
        )

        all_pool_info = []
        for data in list(zip_rpc_response(pool_info_list, response)):
            result = rpc_response_to_result(data[1])
            pool_info = data[0]
            try:
                decoded_data = decode_data(INIT_POOL_TOTAL_SUPPLY_FUNCTION.get_outputs_type(), hex_str_to_bytes(result))
                pool_info["decoded_data"] = decoded_data[0]

            except Exception as e:
                logger.error(
                    f"Decoding pool info failed. "
                    f"pool info: {pool_info}. "
                    f"rpc response: {result}. "
                    f"exception: {e}"
                )
            all_pool_info.append(pool_info)

        pool_history_map = {}
        pool_current_map = {}
        for pool_info in all_pool_info:
            block_number_pool_address = str(pool_info["param_number"]) + "-" + pool_info["param_to"]
            if block_number_pool_address not in pool_history_map:
                pool_history_map[block_number_pool_address] = InitCapitalPoolHistoryDomain(
                    pool_address=pool_info["param_to"],
                    token_address=self._pool_token_map[pool_info["param_to"]],
                    total_asset=0,
                    total_supply=0,
                    total_debt=0,
                    total_debt_share=0,
                    block_number=pool_info["param_number"],
                    block_timestamp=pool_info["block_timestamp"],
                )
            if pool_info["param_data"] == INIT_POOL_TOTAL_SUPPLY_FUNCTION.get_signature():
                pool_history_map[block_number_pool_address].total_supply = pool_info["decoded_data"]
            if pool_info["param_data"] == INIT_POOL_TOTAL_DEBT_FUNCTION.get_signature():
                pool_history_map[block_number_pool_address].total_debt = pool_info["decoded_data"]
            if pool_info["param_data"] == INIT_POOL_TOTAL_DEBT_SHARES_FUNCTION.get_signature():
                pool_history_map[block_number_pool_address].total_debt_share = pool_info["decoded_data"]
            if pool_info["param_data"] == INIT_POOL_TOTAL_ASSETS_FUNCTION.get_signature():
                pool_history_map[block_number_pool_address].total_asset = pool_info["decoded_data"]

        pool_history_list = sorted(list(pool_history_map.values()), key=lambda p: p.block_number)

        for pool_history in pool_history_list:
            if pool_history.pool_address not in pool_current_map:
                pool_current_map[pool_history.pool_address] = InitCapitalPoolUpdateDomain(
                    pool_address=pool_history.pool_address,
                    block_number=pool_history.block_number,
                    block_timestamp=pool_history.block_timestamp,
                    total_asset=0,
                    total_supply=0,
                    total_debt=0,
                    total_debt_share=0,
                )
            pool_current_map[pool_history.pool_address].total_asset = pool_history.total_asset
            pool_current_map[pool_history.pool_address].total_supply = pool_history.total_supply
            pool_current_map[pool_history.pool_address].total_debt = pool_history.total_debt
            pool_current_map[pool_history.pool_address].total_debt_share = pool_history.total_debt_share

        return pool_history_list, list(pool_current_map.values())
