import configparser
import json
import logging
import os
import queue

import eth_abi
from web3 import Web3

from indexer.domain.log import Log
from indexer.domain.token_transfer import ERC721TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordUniswapV3Token
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3 import constants
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Token
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens
from indexer.modules.custom.uniswap_v3.util import load_abi
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_TOKENS.value


class ExportUniSwapV3TokensJob(FilterTransactionDataJob):
    dependency_types = [Log, ERC721TokenTransfer]
    output_types = [AllFeatureValueRecordUniswapV3Token, UniswapV3Token]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = (kwargs["config"].get("db_service"),)
        self._load_config("config.ini")
        self._abi_list = load_abi("abi.json")
        self._liquidity_token_id_blocks = queue.Queue()
        self._exist_token_ids = get_exist_token_ids(self._service[0], self._nft_address)

    def _load_config(self, filename):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._nft_address = config.get("info", "nft_address").lower()
            self._factory_address = config.get("info", "factory_address").lower()
            self._liquidity_topic0_dict = json.loads(config.get("info", "liquidity_topic0_dict"))
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[self._factory_address],
                    topics=list(self._liquidity_topic0_dict.keys()),
                ),
                TopicSpecification(addresses=[self._nft_address]),
            ]
        )

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        # collect the nft_ids which were minted or burned
        mint_token_ids, burn_token_ids, all_token_dict = extract_changed_tokens(
            self._data_buff[ERC721TokenTransfer.type()], self._nft_address
        )
        token_id_liquidity_records = extract_liquidity_logs(
            self._liquidity_topic0_dict, self._data_buff[Log.type()], self._nft_address
        )

        need_collect_value_tokens, want_pool_tokens = gather_collect_infos(
            all_token_dict,
            token_id_liquidity_records,
            burn_token_ids,
            self._exist_token_ids,
        )
        # call owners
        owner_dict = get_owner_dict(
            self._web3,
            self._batch_web3_provider.make_request,
            need_collect_value_tokens,
            self._nft_address,
            self._is_batch,
            self._abi_list,
        )

        # call positions
        token_infos = positions_rpc_requests(
            self._web3,
            self._batch_web3_provider.make_request,
            need_collect_value_tokens,
            self._nft_address,
            self._is_batch,
            self._abi_list,
        )
        # filter the info which call pool needed
        update_exist_tokens, new_nft_info = get_new_nfts(
            token_infos,
            want_pool_tokens,
            self._nft_address,
            self._web3,
            self._batch_web3_provider.make_request,
            need_collect_value_tokens,
            self._factory_address,
            self._is_batch,
            self._abi_list,
        )
        self._exist_token_ids.update(update_exist_tokens)
        for data in new_nft_info:
            self._collect_item(UniswapV3Token.type(), data)

        new_records = parse_token_records(self._exist_token_ids, owner_dict, token_infos, FEATURE_ID)
        for data in new_records:
            self._collect_item(AllFeatureValueRecordUniswapV3Token.type(), data)

    def _process(self):
        self._data_buff[UniswapV3Token.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[AllFeatureValueRecordUniswapV3Token.type()].sort(key=lambda x: x.block_number)


def parse_token_records(token_pool_dict, owner_dict, token_infos, feature_id):
    # one address may have many records in one block
    address_infos = {}

    for data in token_infos:
        block_number = data["block_number"]
        token_id = data["token_id"]
        address = owner_dict[token_id][block_number]

        value = {
            "token_id": token_id,
            "tick_lower": data["tickLower"],
            "tick_upper": data["tickUpper"],
            "fee": data["fee"],
            "liquidity": data["liquidity"],
            "token0": data["token0"],
            "token1": data["token1"],
            "block_number": block_number,
            "pool_address": token_pool_dict[token_id],
        }

        if address not in address_infos.keys():
            address_infos[address] = {}
        if block_number not in address_infos[address]:
            address_infos[address][block_number] = []
        address_infos[address][block_number].append(value)
    result = []
    for address, block in address_infos.items():
        for block_number, data in block.items():
            result.append(
                AllFeatureValueRecordUniswapV3Token(
                    feature_id=feature_id,
                    block_number=block_number,
                    address=address,
                    value=data,
                )
            )
    return result


def gather_collect_infos(all_token_dict, token_id_block, burn_token_ids, exist_token_ids):
    seen = set()
    for token_id, blocks in all_token_dict.items():
        for block_number, to_address in blocks.items():
            seen.add((token_id, block_number))
    for token_id, blocks in token_id_block.items():
        for block_number, to_address in blocks.items():
            seen.add((token_id, block_number))

    need_collect_value_tokens = []
    want_pool_tokens = set()
    for item in seen:
        token_id = item[0]
        block_number = item[1]
        if token_id not in burn_token_ids or burn_token_ids[token_id] < block_number:
            temp = {
                "token_id": token_id,
                "block_number": block_number,
            }
            need_collect_value_tokens.append(temp)
            if token_id not in exist_token_ids:
                want_pool_tokens.add((token_id, block_number))
    return need_collect_value_tokens, want_pool_tokens


def get_owner_dict(web3, make_requests, requests, nft_address, is_batch, abi_list):
    owners = owner_rpc_requests(web3, make_requests, requests, nft_address, is_batch, abi_list)
    owner_dict = {}
    for data in owners:
        owner_dict.setdefault(data["token_id"], {})[data["block_number"]] = data["owner"]
    return owner_dict


def get_new_nfts(
    all_token_infos,
    want_pool_tokens,
    nft_address,
    web3,
    make_requests,
    requests,
    factory_address,
    is_batch,
    abi_list,
):
    result = []
    need_collect_pool_tokens = []
    for info in all_token_infos:
        token_id = info["token_id"]
        block_number = info["block_number"]
        if (token_id, block_number) in want_pool_tokens:
            need_collect_pool_tokens.append(info)

    new_pool_info = get_pool_rpc_requests(web3, make_requests, requests, factory_address, is_batch, abi_list)
    pool_dict = {}
    for data in new_pool_info:
        key = data["token0"] + data["token1"] + str(data["fee"])
        pool_dict[key] = data["pool_address"]
    # get new nft_id info
    update_exist_tokens = {}
    seen = set()

    for data in need_collect_pool_tokens:
        token_id = data["token_id"]
        if (nft_address, token_id) in seen:
            continue
        seen.add((nft_address, token_id))
        key = data["token0"] + data["token1"] + str(data["fee"])
        pool_address = pool_dict[key]
        update_exist_tokens[token_id] = pool_address

        result.append(
            UniswapV3Token(
                nft_address=nft_address,
                token_id=token_id,
                pool_address=pool_address,
                tick_lower=data["tickLower"],
                tick_upper=data["tickUpper"],
                fee=data["fee"],
                called_block_number=data["block_number"],
            )
        )
    return update_exist_tokens, result


def get_exist_token_ids(db_service, nft_address):
    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Tokens.token_id, UniswapV3Tokens.pool_address)
            .filter(
                UniswapV3Tokens.pool_address != None,
                UniswapV3Tokens.nft_address == bytes.fromhex(nft_address[2:]),
            )
            .all()
        )
        history_token = {}
        if result is not None:
            for item in result:
                token_id = (item.token_id,)
                history_token[token_id] = "0x" + item.pool_address.hex()
    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()
    return history_token


def extract_changed_tokens(token_transfers, nft_address):
    mint_tokens_dict = {}
    burn_tokens_dict = {}
    all_tokens_dict = {}
    sorted_transfers = sorted(token_transfers, key=lambda x: (x.block_number, x.log_index))

    for transfer in sorted_transfers:
        token_address = transfer.token_address
        if token_address != nft_address:
            continue
        token_id = transfer.token_id
        block_number = transfer.block_number
        to_address = transfer.to_address
        from_address = transfer.from_address

        if token_id not in all_tokens_dict:
            all_tokens_dict[token_id] = {}
        all_tokens_dict[token_id][block_number] = to_address

        if to_address == constants.ZERO_ADDRESS:
            burn_tokens_dict[token_id] = block_number
        elif from_address == constants.ZERO_ADDRESS:
            mint_tokens_dict[token_id] = block_number

    return mint_tokens_dict, burn_tokens_dict, all_tokens_dict


def extract_liquidity_logs(topic0_dict, logs, nft_address):
    token_id_block = {}

    for log in logs:
        if log.address != nft_address:
            continue

        topic0 = log.topic0
        if topic0 not in topic0_dict:
            continue

        topic_index = topic0_dict[topic0]
        if topic_index == 1:
            token_id_hex = log.topic1
        elif topic_index == 2:
            token_id_hex = log.topic2
        else:
            token_id_hex = log.topic3
        token_id = int(token_id_hex[2:], 16)
        token_id_block.setdefault(token_id, {})[log.block_number] = topic0
    return token_id_block


def build_token_id_method_data(web3, token_ids, nft_address, fn, abi_list):
    parameters = []
    contract = web3.eth.contract(address=Web3.to_checksum_address(nft_address), abi=abi_list)

    for idx, token in enumerate(token_ids):
        token_data = {
            "request_id": idx,
            "param_to": nft_address,
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)

        try:
            # Encode the ABI for the specific token_id
            data = contract.encodeABI(fn_name=fn, args=[token["token_id"]])
            token["param_data"] = data
        except Exception as e:
            logger.error(
                f"Encoding token id {token['token_id']} for function {fn} failed. "
                f"NFT address: {nft_address}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters


def positions_rpc_requests(web3, make_requests, requests, nft_address, is_batch, abi_list):
    if len(requests) == 0:
        return []
    fn_name = "positions"
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_token_id_method_data(web3, requests, nft_address, fn_name, abi_list)

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
            token["nonce"] = decoded_data[0]
            token["operator"] = decoded_data[1]
            token["token0"] = decoded_data[2]
            token["token1"] = decoded_data[3]
            token["fee"] = decoded_data[4]
            token["tickLower"] = decoded_data[5]
            token["tickUpper"] = decoded_data[6]
            token["liquidity"] = decoded_data[7]
            token["feeGrowthInside0LastX128"] = decoded_data[8]
            token["feeGrowthInside1LastX128"] = decoded_data[9]
            token["tokensOwed0"] = decoded_data[10]
            token["tokensOwed1"] = decoded_data[11]

        except Exception as e:
            logger.error(
                f"Decoding positions failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def owner_rpc_requests(web3, make_requests, requests, nft_address, is_batch, abi_list):
    if len(requests) == 0:
        return []
    fn_name = "ownerOf"
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_token_id_method_data(web3, requests, nft_address, fn_name, abi_list)

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
            token["owner"] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding ownerOf failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def build_get_pool_method_data(web3, requests, factory_address, fn, abi_list):
    parameters = []
    contract = web3.eth.contract(address=Web3.to_checksum_address(factory_address), abi=abi_list)

    for idx, token in enumerate(requests):
        token["request_id"] = (idx,)
        token_data = {
            "request_id": idx,
            "param_to": factory_address,
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)
        try:
            # Encode the ABI for the specific token_id
            data = contract.encodeABI(
                fn_name=fn,
                args=[
                    Web3.to_checksum_address(token["token0"]),
                    Web3.to_checksum_address(token["token1"]),
                    token["fee"],
                ],
            )
            token["param_data"] = data
        except Exception as e:
            logger.error(
                f"Encoding token0 {token['token0']} token1 {token['token1']}  fee {token['fee']}  for function {fn} failed. "
                f"contract address: {factory_address}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters


def get_pool_rpc_requests(web3, make_requests, requests, factory_address, is_batch, abi_list):
    if len(requests) == 0:
        return []
    fn_name = "getPool"
    function_abi = next(
        (abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"),
        None,
    )
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_get_pool_method_data(web3, requests, factory_address, fn_name, abi_list)
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
            token["pool_address"] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding getPool failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def build_no_input_method_data(web3, requests, fn, block_number, abi_list):
    parameters = []

    for idx, token in enumerate(requests):
        token["request_id"] = (idx,)
        token_data = {
            "request_id": idx,
            "param_to": token["pool_address"],
            "param_number": hex(block_number),
        }
        token.update(token_data)
        try:
            # Encode the ABI for the specific token_id
            token["param_data"] = web3.eth.contract(
                address=Web3.to_checksum_address(token["pool_address"]), abi=abi_list
            ).encodeABI(fn_name=fn)
        except Exception as e:
            logger.error(
                f"Encoding token0 {token['token0']} token1 {token['token1']}  fee {token['fee']}  for function {fn} failed. "
                f"contract address: {token['pool_address']}. "
                f"Exception: {e}."
            )

        parameters.append(token)
    return parameters
