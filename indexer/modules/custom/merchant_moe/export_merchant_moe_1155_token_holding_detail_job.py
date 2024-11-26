import json
import logging
from collections import defaultdict

from common.utils.abi_code_utils import decode_data
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domains.log import Log
from indexer.domains.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.merchant_moe.abi import (
    DEPOSITED_TO_BINS_EVENT,
    GET_ACTIVE_ID_FUNCTION,
    GET_BIN_FUNCTION,
    GET_BIN_STEP_FUNCTION,
    GET_TOKENX_FUNCTION,
    GET_TOKENY_FUNCTION,
    LB_PAIR_CREATED_EVENT,
    SWAP_EVENT,
    TOTAL_SUPPLY_FUNCTION,
    TRANSFER_BATCH_EVNET,
    WITHDRAWN_FROM_BINS_EVENT,
)
from indexer.modules.custom.merchant_moe.domains.erc1155_token_holding import (
    MerchantMoeErc1155TokenCurrentHolding,
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenHolding,
    MerchantMoeErc1155TokenSupply,
)
from indexer.modules.custom.merchant_moe.domains.merchant_moe import (
    MerchantMoePool,
    MerchantMoePoolCurrentStatus,
    MerchantMoePoolRecord,
    MerchantMoeTokenBin,
    MerchantMoeTokenCurrentBin,
)
from indexer.modules.custom.merchant_moe.models.feature_merchant_moe_pool import FeatureMerchantMoePools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)

FUNCTION_LIST = [
    TOTAL_SUPPLY_FUNCTION,
    GET_BIN_FUNCTION,
    GET_TOKENX_FUNCTION,
    GET_TOKENY_FUNCTION,
    GET_ACTIVE_ID_FUNCTION,
    GET_BIN_STEP_FUNCTION,
]
ABI_LIST = [f.get_abi() for f in FUNCTION_LIST]


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
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self._exist_pool = get_exist_pools(self._service)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

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

    def _process(self, **kwargs):
        # collect pools
        self._collect_pools()

        token_balances = self._data_buff[TokenBalance.type()]

        erc115_token_balances = [
            tb for tb in token_balances if tb.token_type == "ERC1155" and tb.token_address in self._exist_pool
        ]
        # Maybe it can be removed
        erc115_token_balances.sort(key=lambda x: x.block_number)

        position_token_address_request_token_id_dict = defaultdict(dict)
        current_holding_dict = {}

        for erc115_token_balance in erc115_token_balances:
            token_id_request_dict = {
                "block_number": erc115_token_balance.block_number,
                "block_timestamp": erc115_token_balance.block_timestamp,
                "token_id": erc115_token_balance.token_id,
            }

            position_token_address_request_token_id_dict[erc115_token_balance.token_address][
                erc115_token_balance.token_id, erc115_token_balance.block_number
            ] = token_id_request_dict
            # current holding
            holding_common_params = {
                "position_token_address": erc115_token_balance.token_address,
                "wallet_address": erc115_token_balance.address,
                "balance": erc115_token_balance.balance,
                **token_id_request_dict,
            }

            merchant_moe_erc_token_holding = MerchantMoeErc1155TokenHolding(**holding_common_params)
            self._collect_domain(merchant_moe_erc_token_holding)

            merchant_moe_erc_token_current_holding = MerchantMoeErc1155TokenCurrentHolding(**holding_common_params)
            # covered by the latest one
            current_holding_dict[erc115_token_balance.token_address, erc115_token_balance.token_id] = (
                merchant_moe_erc_token_current_holding
            )

        self._collect_domains(current_holding_dict.values())

        # collect total supply, total_supply changes only in the case of changing of the erc115 token
        for position_token_address, request_token_id_dict in position_token_address_request_token_id_dict.items():
            total_supply_requests = []
            for _, request_dict in request_token_id_dict.items():
                total_supply_requests.append(request_dict)

            total_supply_result = batch_get_total_supply(
                self._web3,
                self._batch_web3_provider.make_request,
                total_supply_requests,
                position_token_address,
                self._is_batch,
                ABI_LIST,
            )

            current_supply_dict = {}

            total_supply_result.sort(key=lambda x: x["block_number"])
            for supply_result in total_supply_result:
                supply_common_params = {
                    "position_token_address": position_token_address,
                    "token_id": supply_result["token_id"],
                    "total_supply": supply_result["totalSupply"],
                    "block_number": supply_result["block_number"],
                    "block_timestamp": supply_result["block_timestamp"],
                }
                merchant_moe_erc_token_supply = MerchantMoeErc1155TokenSupply(**supply_common_params)
                self._collect_domain(merchant_moe_erc_token_supply)
                merchant_moe_erc_token_current_supply = MerchantMoeErc1155TokenCurrentSupply(**supply_common_params)
                current_supply_dict[position_token_address, supply_result["token_id"]] = (
                    merchant_moe_erc_token_current_supply
                )

            self._collect_domains(current_supply_dict.values())

        # collect bins, which will change also in the case of swap
        logs = self._data_buff["log"]
        for log in logs:
            if log.topic0 == SWAP_EVENT.get_signature():
                decode_dict = SWAP_EVENT.decode_log(log)
                token_id = decode_dict["id"]

                token_id_request_dict = {
                    "block_number": log.block_number,
                    "block_timestamp": log.block_timestamp,
                    "token_id": token_id,
                }
                position_token_address_request_token_id_dict[log.address][
                    token_id, log.block_number
                ] = token_id_request_dict

        for position_token_address, request_token_id_dict in position_token_address_request_token_id_dict.items():
            total_bins_requests = []
            for _, request_dict in request_token_id_dict.items():
                total_bins_requests.append(request_dict)

            current_bins_dict = {}
            total_bin_result = batch_get_bin(
                self._web3,
                self._batch_web3_provider.make_request,
                total_bins_requests,
                position_token_address,
                self._is_batch,
                ABI_LIST,
            )
            total_bin_result.sort(key=lambda x: x["block_number"])
            for bins_result in total_bin_result:
                bin_common_params = {
                    "position_token_address": position_token_address,
                    "token_id": bins_result["token_id"],
                    "block_number": bins_result["block_number"],
                    "block_timestamp": bins_result["block_timestamp"],
                    "reserve0_bin": bins_result["reserve0_bin"],
                    "reserve1_bin": bins_result["reserve1_bin"],
                }

                mer_chant_moe_token_bin = MerchantMoeTokenBin(**bin_common_params)
                self._collect_domain(mer_chant_moe_token_bin)

                mer_chant_moe_token_current_bin = MerchantMoeTokenCurrentBin(**bin_common_params)
                current_bins_dict[position_token_address, bins_result["token_id"]] = mer_chant_moe_token_current_bin
            self._collect_domains(current_bins_dict.values())

        # get active id and step
        if logs is not None and len(logs) > 0:
            self._batch_work_executor.execute(
                logs, self._collect_pool_batch, total_items=len(logs), split_method=split_logs
            )
            self._batch_work_executor.wait()

    def _collect_pools(self):
        create_pool_topic0 = LB_PAIR_CREATED_EVENT.get_signature()
        logs = self._data_buff["log"]
        for log in logs:
            if log.topic0 == create_pool_topic0:
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
            self._web3, self._batch_web3_provider.make_request, pool_array, self._is_batch, ABI_LIST
        )

        active_id_array = batch_get_pool_active_id(
            self._web3, self._batch_web3_provider.make_request, bin_step_array, self._is_batch, ABI_LIST
        )
        current_pool_data = None
        for data in active_id_array:
            entity = MerchantMoePoolRecord(
                pool_address=data["token_address"],
                active_id=data["getActiveId"],
                bin_step=data["getBinStep"],
                block_number=data["block_number"],
                block_timestamp=data["block_timestamp"],
            )
            if current_pool_data is None or current_pool_data.block_number < entity.block_number:
                current_pool_data = MerchantMoePoolCurrentStatus(
                    pool_address=entity.pool_address,
                    active_id=entity.active_id,
                    bin_step=entity.bin_step,
                    block_number=entity.block_number,
                    block_timestamp=entity.block_timestamp,
                )
            self._collect_item(MerchantMoePoolRecord.type(), entity)
        if current_pool_data:
            self._collect_item(MerchantMoePoolCurrentStatus.type(), current_pool_data)


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
            decoded_data = decode_data(output_types, hex_str_to_bytes(value))
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
            decoded_data = decode_data(output_types, hex_str_to_bytes(value))
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
            decoded_data = decode_data(output_types, hex_str_to_bytes(value))
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
    return history_pools
