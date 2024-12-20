import logging

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.collection_utils import distinct_collections_by_group
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.merchant_moe.abi import (
    DEPOSITED_TO_BINS_EVENT,
    GET_ACTIVE_ID_FUNCTION,
    GET_BIN_FUNCTION,
    GET_BIN_STEP_FUNCTION,
    LB_PAIR_CREATED_EVENT,
    SWAP_EVENT,
    TOTAL_SUPPLY_FUNCTION,
    TRANSFER_BATCH_EVNET,
    WITHDRAWN_FROM_BINS_EVENT,
)
from hemera_udf.merchant_moe.domains import (
    MerchantMoeErc1155TokenCurrentHolding,
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenHolding,
    MerchantMoeErc1155TokenSupply,
    MerchantMoePool,
    MerchantMoePoolCurrentStatus,
    MerchantMoePoolRecord,
    MerchantMoeTokenBin,
    MerchantMoeTokenCurrentBin,
)
from hemera_udf.merchant_moe.models.feature_merchant_moe_pool import FeatureMerchantMoePools

logger = logging.getLogger(__name__)


class ExportMerchantMoe1155LiquidityJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, Log]
    output_types = [
        MerchantMoeErc1155TokenHolding,
        MerchantMoeErc1155TokenCurrentHolding,
        MerchantMoeErc1155TokenSupply,
        MerchantMoeErc1155TokenCurrentSupply,
        MerchantMoeTokenBin,
        MerchantMoeTokenCurrentBin,
        MerchantMoePool,
        MerchantMoePoolCurrentStatus,
        MerchantMoePoolRecord,
    ]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._exist_pool = get_exist_pools(self._service)
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        DEPOSITED_TO_BINS_EVENT.get_signature(),
                        WITHDRAWN_FROM_BINS_EVENT.get_signature(),
                        TRANSFER_BATCH_EVNET.get_signature(),
                        SWAP_EVENT.get_signature(),
                        LB_PAIR_CREATED_EVENT.get_signature(),
                    ]
                ),
            ]
        )

    def extract_current_status(self, records, current_status_domain, keys):
        results = []
        last_records = distinct_collections_by_group(collections=records, group_by=keys, max_key="block_number")
        for last_record in last_records:
            record = current_status_domain(**vars(last_record))
            results.append(record)
        return results

    def _process(self, **kwargs):
        # 1.collect pools
        self._collect_pools()

        # 2.collect holdings/total supply/ bin
        token_balances = self._data_buff[TokenBalance.type()]
        erc115_token_balances = [
            tb for tb in token_balances if tb.token_type == "ERC1155" and tb.token_address in self._exist_pool
        ]
        # Maybe it can be removed
        erc115_token_balances.sort(key=lambda x: x.block_number)

        # all positions that need to call
        call_dicts = {}

        records = []
        for erc115_token_balance in erc115_token_balances:
            # current holding
            position_token_address = erc115_token_balance.token_address
            token_id = erc115_token_balance.token_id
            block_number = erc115_token_balance.block_number
            holding_common_params = {
                "position_token_address": position_token_address,
                "wallet_address": erc115_token_balance.address,
                "balance": erc115_token_balance.balance,
                "block_number": block_number,
                "block_timestamp": erc115_token_balance.block_timestamp,
                "token_id": token_id,
            }

            merchant_moe_erc_token_holding = MerchantMoeErc1155TokenHolding(**holding_common_params)
            records.append(merchant_moe_erc_token_holding)

            # add call_dict
            call_dict = {
                "target": position_token_address,
                "parameters": [token_id],
                "block_number": block_number,
                "user_defined_k": erc115_token_balance.block_timestamp,
            }
            call_dicts[position_token_address, token_id, block_number] = call_dict

        current_status = self.extract_current_status(
            records, MerchantMoeErc1155TokenCurrentHolding, ["position_token_address", "token_id"]
        )
        self._collect_domains(records)
        self._collect_domains(current_status)

        # collect total supply, total_supply changes only in the case of changing of the erc115 token
        supply_call_list = []
        for call_dict in call_dicts.values():
            call = Call(function_abi=TOTAL_SUPPLY_FUNCTION, **call_dict)
            supply_call_list.append(call)

        self.multi_call_helper.execute_calls(supply_call_list)

        supply_records = []
        for supply_call in supply_call_list:
            position_token_address = supply_call.target.lower()
            token_id = supply_call.parameters[0]
            block_number = supply_call.block_number
            block_timestamp = supply_call.user_defined_k
            returns = supply_call.returns
            total_supply = returns.get("totalSupply")

            supply_common_params = {
                "position_token_address": position_token_address,
                "token_id": token_id,
                "total_supply": total_supply,
                "block_number": block_number,
                "block_timestamp": block_timestamp,
            }
            merchant_moe_erc_token_supply = MerchantMoeErc1155TokenSupply(**supply_common_params)
            supply_records.append(merchant_moe_erc_token_supply)

        current_supply_records = self.extract_current_status(
            supply_records, MerchantMoeErc1155TokenCurrentSupply, ["position_token_address", "token_id"]
        )
        self._collect_domains(current_supply_records)
        self._collect_domains(supply_records)

        # collect bins, which will change also in the case of swap
        logs = self._data_buff["log"]
        for log in logs:
            if log.topic0 == SWAP_EVENT.get_signature():
                decode_dict = SWAP_EVENT.decode_log(log)
                token_id = decode_dict["id"]
                position_token_address = log.address
                block_number = log.block_number

                call_dict = {
                    "target": position_token_address,
                    "parameters": [token_id],
                    "block_number": block_number,
                    "user_defined_k": log.block_timestamp,
                }
                call_dicts[position_token_address, token_id, block_number] = call_dict

        bin_call_list = []
        for call_dict in call_dicts.values():
            call = Call(function_abi=GET_BIN_FUNCTION, **call_dict)
            bin_call_list.append(call)

        self.multi_call_helper.execute_calls(bin_call_list)

        bin_records = []
        for bin_call in bin_call_list:
            position_token_address = bin_call.target.lower()
            token_id = bin_call.parameters[0]
            block_number = bin_call.block_number
            block_timestamp = bin_call.user_defined_k
            returns = bin_call.returns

            reserve0_bin = returns.get("binReserveX")
            reserve1_bin = returns.get("binReserveY")

            bin_common_params = {
                "position_token_address": position_token_address,
                "token_id": token_id,
                "block_number": block_number,
                "block_timestamp": block_timestamp,
                "reserve0_bin": reserve0_bin,
                "reserve1_bin": reserve1_bin,
            }

            mer_chant_moe_token_bin = MerchantMoeTokenBin(**bin_common_params)
            bin_records.append(mer_chant_moe_token_bin)

        current_bin_records = self.extract_current_status(
            bin_records, MerchantMoeTokenCurrentBin, ["position_token_address", "token_id"]
        )
        self._collect_domains(current_bin_records)
        self._collect_domains(bin_records)

        # 3. get active id and step
        self.get_active_id_and_bin_step()

    def _collect_pools(self):
        logs = self._data_buff["log"]
        for log in logs:
            if log.topic0 == LB_PAIR_CREATED_EVENT.get_signature():
                decoded_log_dict = LB_PAIR_CREATED_EVENT.decode_log(log)
                position_token_address = decoded_log_dict["LBPair"]
                if position_token_address not in self._exist_pool:
                    self._exist_pool.append(position_token_address)
                    mer_chant_moe_pool = MerchantMoePool(
                        position_token_address=position_token_address,
                        token0_address=decoded_log_dict["tokenX"],
                        token1_address=decoded_log_dict["tokenY"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                    )
                    self._collect_domain(mer_chant_moe_pool)

    def get_active_id_and_bin_step(self):
        global bin_step_call, bin_step_call
        logs = self._data_buff["log"]

        call_dict_list = {}
        for log in logs:
            if log.address in self._exist_pool:
                position_token_address = log.address
                call_dict = {
                    "target": position_token_address,
                    "block_number": log.block_number,
                    "user_defined_k": log.block_timestamp,
                }

                call_dict_list[position_token_address, log.block_number] = call_dict

        call_dicts = call_dict_list.values()
        active_id_call_list = []
        bin_step_call_list = []

        for call_dict in call_dicts:
            call = Call(function_abi=GET_ACTIVE_ID_FUNCTION, **call_dict)
            active_id_call_list.append(call)

            call = Call(function_abi=GET_BIN_STEP_FUNCTION, **call_dict)
            bin_step_call_list.append(call)

        self.multi_call_helper.execute_calls(active_id_call_list)
        self.multi_call_helper.execute_calls(bin_step_call_list)

        records = []

        for active_id_call, bin_step_call in zip(active_id_call_list, bin_step_call_list):
            pool_address = active_id_call.target.lower()
            active_id = active_id_call.returns.get("activeId")
            bin_step = bin_step_call.returns.get("binStep")

            record = MerchantMoePoolRecord(
                pool_address=pool_address,
                active_id=active_id,
                bin_step=bin_step,
                block_number=active_id_call.block_number,
                block_timestamp=active_id_call.user_defined_k,
            )
            records.append(record)

        current_records = self.extract_current_status(records, MerchantMoePoolCurrentStatus, keys=["pool_address"])
        self._collect_domains(records)
        self._collect_domains(current_records)


def get_exist_pools(db_service):
    if not db_service:
        return []

    session = db_service.get_service_session()
    try:
        result = session.query(FeatureMerchantMoePools).all()
        history_pools = set()
        if result is not None:
            for item in result:
                history_pools.add(bytes_to_hex_str(item.position_token_address))
    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return list(history_pools)
