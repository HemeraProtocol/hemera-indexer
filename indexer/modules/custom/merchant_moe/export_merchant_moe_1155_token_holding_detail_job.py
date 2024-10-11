import json
import logging
from collections import defaultdict

import eth_abi

from indexer.domain.log import Log
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.merchant_moe import constants
from indexer.modules.custom.merchant_moe.domain.merchant_moe import (
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenSupply,
    MerChantMoePool,
    MerChantMoePoolCurrentStatu,
    MerChantMoePoolRecord,
    MerChantMoeTokenBin,
    MerChantMoeTokenCurrentBin,
)
from indexer.modules.custom.merchant_moe.models.feature_merchant_moe_pool import FeatureMerChantMoePools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.MERCHANT_MOE_1155_LIQUIDITY.value


class ExportMerchantMoe1155LiquidityJob(FilterTransactionDataJob):
    dependency_types = [TokenBalance, Log]
    output_types = [
        MerchantMoeErc1155TokenSupply,
        MerchantMoeErc1155TokenCurrentSupply,
        MerChantMoeTokenBin,
        MerChantMoeTokenCurrentBin,
        MerChantMoePool,
        MerChantMoePoolCurrentStatu,
        MerChantMoePoolRecord,
    ]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._need_collected_list = constants.LIQUIDITY_LIST
        self._exist_pool = get_exist_pools(self._service)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=self._need_collected_list),
            ]
        )

    def _collect(self, **kwargs):
        if self._need_collected_list is None or len(self._need_collected_list) == 0:
            return
        token_balances = self._data_buff[TokenBalance.type()]
        if token_balances is not None and len(token_balances) > 0:
            self._batch_work_executor.execute(
                token_balances,
                self._collect_token_batch,
                total_items=len(token_balances),
                split_method=split_token_balances,
            )

            self._batch_work_executor.wait()
        logs = self._data_buff[Log.type()]
        if logs is not None and len(logs) > 0:
            self._batch_work_executor.execute(
                logs, self._collect_pool_batch, total_items=len(logs), split_method=split_logs
            )
            self._batch_work_executor.wait()

    def _collect_token_batch(self, token_balances) -> None:
        if token_balances is None or len(token_balances) == 0:
            return
        token_address = next(iter(token_balances))
        infos = token_balances[token_address]
        if infos is None or len(infos) == 0:
            return
        # check the token_address is in merchant_moe
        if token_address not in self._exist_pool:
            if infos[0].token_id is None or infos[0].token_id < 0 or infos[0].token_type != "ERC1155":
                return
            requests = [
                {
                    "block_number": infos[0].block_number,
                    "address": token_address,
                }
            ]

            token0_infos = common_utils.simple_get_rpc_requests(
                self._web3,
                self._batch_web3_provider.make_request,
                requests,
                self._is_batch,
                constants.ABI_LIST,
                "getTokenX",
                "address",
                self._batch_size,
                self._max_worker,
            )

            if len(token0_infos) == 0 or "getTokenX" not in token0_infos[0] or token0_infos[0]["getTokenX"] is None:
                return
            token1_infos = common_utils.simple_get_rpc_requests(
                self._web3,
                self._batch_web3_provider.make_request,
                requests,
                self._is_batch,
                constants.ABI_LIST,
                "getTokenY",
                "address",
                self._batch_size,
                self._max_worker,
            )
            if len(token1_infos) == 0 or "getTokenY" not in token1_infos[0] or token1_infos[0]["getTokenY"] is None:
                return
            self._exist_pool.add(token_address)
            self._collect_item(
                MerChantMoePool.type(),
                MerChantMoePool(
                    position_token_address=token_address,
                    token0_address=token1_infos[0]["getTokenX"],
                    token1_address=token1_infos[0]["getTokenY"],
                    block_number=infos[0].block_number,
                    block_timestamp=infos[0].block_timestamp,
                ),
            )

        need_call_list = []
        token_id_info_set = set()
        for token_balance in infos:
            token_address = token_balance.token_address
            block_number = token_balance.block_number
            block_timestamp = token_balance.block_timestamp
            token_id = token_balance.token_id
            if (token_id, block_number) not in token_id_info_set:
                token_id_info_set.add((token_id, block_number))
                need_call_list.append(
                    {
                        "block_number": block_number,
                        "block_timestamp": block_timestamp,
                        "token_id": token_id,
                    }
                )
        total_supply_dtos = batch_get_total_supply(
            self._web3,
            self._batch_web3_provider.make_request,
            need_call_list,
            token_address,
            self._is_batch,
            constants.ABI_LIST,
        )
        total_bin_dtos = batch_get_bin(
            self._web3,
            self._batch_web3_provider.make_request,
            need_call_list,
            token_address,
            self._is_batch,
            constants.ABI_LIST,
        )
        current_total_supply_dict = {}
        current_token_bin_dict = {}
        for data in total_bin_dtos:
            token_id = data["token_id"]
            block_number = data["block_number"]
            block_timestamp = data["block_timestamp"]
            total_supply = data["totalSupply"]
            reserve0_bin = data["reserve0_bin"]
            reserve1_bin = data["reserve1_bin"]
            common_data = {
                "position_token_address": token_address,
                "token_id": token_id,
                "block_number": block_number,
                "block_timestamp": block_timestamp,
            }

            key = token_id
            if key not in current_total_supply_dict or block_number > current_total_supply_dict[key].block_number:
                current_total_supply_dict[key] = MerchantMoeErc1155TokenCurrentSupply(
                    **common_data,
                    total_supply=total_supply,
                )
            if key not in current_token_bin_dict or block_number > current_token_bin_dict[key].block_number:
                current_token_bin_dict[key] = MerChantMoeTokenCurrentBin(
                    **common_data,
                    reserve0_bin=reserve0_bin,
                    reserve1_bin=reserve1_bin,
                )
            self._collect_item(
                MerchantMoeErc1155TokenSupply.type(),
                MerchantMoeErc1155TokenSupply(
                    **common_data,
                    total_supply=total_supply,
                ),
            )
            self._collect_item(
                MerChantMoeTokenBin.type(),
                MerChantMoeTokenBin(
                    **common_data,
                    reserve0_bin=reserve0_bin,
                    reserve1_bin=reserve1_bin,
                ),
            )
        for data in current_total_supply_dict.values():
            self._collect_item(MerchantMoeErc1155TokenCurrentSupply.type(), data)
        for data in current_token_bin_dict.values():
            self._collect_item(MerChantMoeTokenCurrentBin.type(), data)

    def _collect_pool_batch(self, log_dict) -> None:
        if log_dict is None or len(log_dict) == 0:
            return
        token_address = next(iter(log_dict))
        logs = log_dict[token_address]
        if logs is None or len(logs) == 0:
            return
        blocks_set = set()
        for log in logs:
            token_address = log.address
            if token_address not in self._exist_pool:
                continue
            block_number = log.block_number
            block_timestamp = log.block_timestamp
            blocks_set.add((token_address, block_number, block_timestamp))

        pool_array = []
        for token_address, block_number, block_timestamp in blocks_set:
            pool_array.append(
                {
                    "block_number": block_number,
                    "block_timestamp": block_timestamp,
                    "token_address": token_address,
                }
            )
        if pool_array is None or len(pool_array) == 0:
            return
        bin_step_array = batch_get_pool_bin_step(
            self._web3, self._batch_web3_provider.make_request, pool_array, self._is_batch, constants.ABI_LIST
        )

        active_id_array = batch_get_pool_active_id(
            self._web3, self._batch_web3_provider.make_request, bin_step_array, self._is_batch, constants.ABI_LIST
        )
        current_pool_data = None
        for data in active_id_array:
            entity = MerChantMoePoolRecord(
                pool_address=data["token_address"],
                active_id=data["getActiveId"],
                bin_step=data["getBinStep"],
                block_number=data["block_number"],
                block_timestamp=data["block_timestamp"],
            )
            if current_pool_data is None or current_pool_data.block_number < entity.block_number:
                current_pool_data = MerChantMoePoolCurrentStatu(
                    pool_address=entity.pool_address,
                    active_id=entity.active_id,
                    bin_step=entity.bin_step,
                    block_number=entity.block_number,
                    block_timestamp=entity.block_timestamp,
                )
            self._collect_item(MerChantMoePoolRecord.type(), entity)
        if current_pool_data:
            self._collect_item(MerChantMoePoolCurrentStatu.type(), current_pool_data)

    def _process(self, **kwargs):

        self._data_buff[MerchantMoeErc1155TokenSupply.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoeTokenBin.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerchantMoeErc1155TokenCurrentSupply.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoeTokenCurrentBin.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoePoolCurrentStatu.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoePoolRecord.type()].sort(key=lambda x: x.block_number)
        self._data_buff[MerChantMoePool.type()].sort(key=lambda x: x.block_number)


def split_token_balances(token_balances):
    token_balance_dict = defaultdict(list)
    for data in token_balances:
        token_balance_dict[data.token_address].append(data)

    for token_address, data in token_balance_dict.items():
        yield {token_address: data}


def split_logs(logs):
    log_dict = defaultdict(list)
    for data in logs:
        log_dict[data.address].append(data)

    for address, data in log_dict.items():
        yield {address: data}


def batch_get_bin(web3, make_requests, requests, nft_address, is_batch, abi_list):
    fn_name = "getBin"
    if len(requests) == 0:
        return []
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_one_input_one_output_method_data(web3, requests, nft_address, fn_name, abi_list)

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token["reserve0_bin"] = decoded_data[0]
            token["reserve1_bin"] = decoded_data[1]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def batch_get_total_supply(web3, make_requests, requests, nft_address, is_batch, abi_list):
    fn_name = "totalSupply"
    if len(requests) == 0:
        return []
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_one_input_one_output_method_data(web3, requests, nft_address, fn_name, abi_list)

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token[fn_name] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def batch_get_pool_bin_step(web3, make_requests, requests, is_batch, abi_list):
    return batch_get_pool_int(web3, make_requests, requests, is_batch, abi_list, "getBinStep")


def batch_get_pool_active_id(web3, make_requests, requests, is_batch, abi_list):
    return batch_get_pool_int(web3, make_requests, requests, is_batch, abi_list, "getActiveId")


def batch_get_pool_int(web3, make_requests, requests, is_batch, abi_list, fn_name):
    if len(requests) == 0:
        return []
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_no_input_method_data(web3, requests, fn_name, abi_list, "token_address")

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token[fn_name] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def get_exist_pools(db_service):
    if not db_service:
        return []

    session = db_service.get_service_session()
    try:
        result = session.query(FeatureMerChantMoePools).all()
        history_pools = set()
        if result is not None:
            for item in result:
                history_pools.add(bytes_to_hex_str(item.position_token_address))
    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return history_pools
