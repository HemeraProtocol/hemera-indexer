import json
import logging
from dataclasses import asdict
from typing import Dict, List

from eth_abi import abi

from common.utils.format_utils import to_snake_case
from enumeration.record_level import RecordLevel
from enumeration.token_type import TokenType
from indexer.domain import dataclass_to_dict, dict_to_dataclass
from indexer.domain.log import Log
from indexer.domain.token import Token, UpdateToken
from indexer.domain.token_transfer import (
    ERC20TokenTransfer,
    ERC721TokenTransfer,
    ERC1155TokenTransfer,
    TokenTransfer,
    extract_transfer_from_log,
)
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.modules.bridge.signature import function_abi_to_4byte_selector_str
from indexer.utils.abi import encode_abi
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc, generate_eth_call_json_rpc_without_block_number
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()

NAME_ABI_FUNCTION = {
    "constant": True,
    "inputs": [],
    "name": "name",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

SYMBOL_ABI_FUNCTION = {
    "constant": True,
    "inputs": [],
    "name": "symbol",
    "outputs": [{"name": "", "type": "string"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

DECIMALS_ABI_FUNCTION = {
    "constant": True,
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint8"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

TOTAL_SUPPLY_ABI_FUNCTION = {
    "constant": True,
    "inputs": [],
    "name": "totalSupply",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

OWNER_OF_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "tokenId", "type": "uint256"}],
    "name": "ownerOf",
    "outputs": [{"name": "owner", "type": "address"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

TOKEN_URI_ABI_FUNCTION = {
    "constant": True,
    "inputs": [{"name": "tokenId", "type": "uint256"}],
    "name": "tokenURI",
    "outputs": [{"name": "uri", "type": "address"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function",
}

abi_mapping = {
    "name": NAME_ABI_FUNCTION,
    "symbol": SYMBOL_ABI_FUNCTION,
    "decimals": DECIMALS_ABI_FUNCTION,
    "totalSupply": TOTAL_SUPPLY_ABI_FUNCTION,
    "ownerOf": OWNER_OF_ABI_FUNCTION,
    "tokenURI": TOKEN_URI_ABI_FUNCTION,
}


class ExportTokensAndTransfersJob(BaseExportJob):
    output_transfer_types = [
        ERC20TokenTransfer,
        ERC721TokenTransfer,
        ERC1155TokenTransfer,
    ]
    output_token_types = [Token, UpdateToken]

    dependency_types = [Log]
    output_types = output_transfer_types + output_token_types

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self._token_addresses = set()
        self._token_transfers = []

    def _start(self):
        super()._start()

    def _end(self):
        super()._end()
        self._token_addresses.clear()
        self._token_transfers.clear()

    def _collect(self, **kwargs):
        self._batch_work_executor.execute(
            self._data_buff[Log.type()],
            self._extract_batch,
            total_items=len(self._data_buff[Log.type()]),
        )
        self._batch_work_executor.wait()

        token_transfers = self._data_buff[TokenTransfer.type()]

        token_dict: Dict[str, Token] = {}
        new_token_dict: Dict[str, Token] = {}
        old_token_dict: Dict[str, Token] = {}
        for transfer in token_transfers:
            key = transfer.token_address
            if key not in token_dict or transfer.block_number > token_dict[key].block_number:
                token_dict[key] = Token(
                    address=transfer.token_address,
                    token_type=transfer.token_type,
                    name=None,
                    symbol=None,
                    decimals=None,
                    block_number=transfer.block_number,
                )

        for address, token in token_dict.items():
            if address not in self.tokens:
                new_token_dict[address] = token
            else:
                old_token_dict[address] = token

        self._batch_work_executor.execute(
            [dataclass_to_dict(x) for x in new_token_dict.values()],
            self._export_token_info_batch,
            total_items=len(new_token_dict.values()),
        )
        self._batch_work_executor.wait()

        for token in self.get_buff()[Token.type()]:
            self.tokens[token.address] = asdict(token)

        filtered_old_tokens = [token for token in token_dict.values() if token.token_type != TokenType.ERC1155.value]
        self._batch_work_executor.execute(
            [dataclass_to_dict(x) for x in filtered_old_tokens],
            self._export_token_total_supply_batch,
            total_items=len(filtered_old_tokens),
        )
        self._batch_work_executor.wait()

        self._batch_work_executor.execute(
            token_transfers,
            self._generate_token_transfers,
            total_items=len(token_transfers),
        )
        self._batch_work_executor.wait()

    def _extract_batch(self, logs):
        token_transfers = extract_tokens_and_token_transfers(logs)
        for transfer in token_transfers:
            self._collect_item(TokenTransfer.type(), transfer)

    def _generate_token_transfers(self, token_transfers):
        for transfer in token_transfers:
            if transfer.token_id is None:
                transfer.token_type = self.tokens[transfer.token_address]["token_type"]
            self._collect_domain(transfer.to_specific_transfer())

    def _export_token_info_batch(self, tokens):
        new_tokens = tokens_info_rpc_requests(self._batch_web3_provider.make_request, tokens, self._is_batch)
        for token in new_tokens:
            self._collect_item(Token.type(), dict_to_dataclass(token, Token))

    def _export_token_total_supply_batch(self, tokens):
        token_updates = tokens_total_supply_rpc_requests(self._batch_web3_provider.make_request, tokens, self._is_batch)
        for token in token_updates:
            if token.get("total_supply") is not None:
                self._collect_item(UpdateToken.type(), dict_to_dataclass(token, UpdateToken))

    def _process(self):
        for token_transfer_type in self.output_transfer_types:
            if token_transfer_type in self._data_buff:
                self._data_buff[token_transfer_type.type()].sort(
                    key=lambda x: (x.block_number, x.transaction_hash, x.log_index)
                )


def extract_tokens_and_token_transfers(logs: List[Log]):
    token_transfers = [transfer for log in logs for transfer in extract_transfer_from_log(log)]
    return token_transfers


def build_rpc_method_data(tokens, fn, arguments=None):
    arguments = arguments or []
    NAME_ABI_FUNCTION = abi_mapping.get(fn)

    for index, token in enumerate(tokens):
        token.update(
            {
                "param_to": token["address"],
                "param_data": "0x",
                "param_number": hex(token["block_number"]),
                "data_type": "",
                "request_id": index,
            }
        )
        token["param_data"] = encode_abi(
            NAME_ABI_FUNCTION,
            arguments,
            function_abi_to_4byte_selector_str(NAME_ABI_FUNCTION),
        )
        token["data_type"] = NAME_ABI_FUNCTION["outputs"][0]["type"]

    return tokens


def tokens_total_supply_rpc_requests(make_requests, tokens, is_batch):
    fn_name = "totalSupply"
    token_name_rpc = list(generate_eth_call_json_rpc_without_block_number(build_rpc_method_data(tokens, fn_name)))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    res = []
    for data in list(zip_rpc_response(tokens, response)):
        result = rpc_response_to_result(data[1])

        token = data[0]
        value = result[2:] if result is not None else None
        try:
            token["total_supply"] = abi.decode(["uint256"], bytes.fromhex(value))[0]
        except Exception as e:
            logger.warning(
                f"Decoding token {fn_name} failed. " f"token: {token}. " f"rpc response: {result}. " f"exception: {e}"
            )
            token["total_supply"] = None
    return tokens


def tokens_info_rpc_requests(make_requests, tokens, is_batch):
    function_call = {
        "name": [],
        "symbol": [],
        "decimals": [],
        "totalSupply": [],
        "ownerOf": [1],
        "tokenURI": [1],
    }

    for fn_name in function_call.keys():
        token_name_rpc = list(
            generate_eth_call_json_rpc_without_block_number(
                build_rpc_method_data(tokens, fn_name, function_call[fn_name])
            )
        )

        if len(token_name_rpc) == 0:
            continue

        if is_batch:
            response = make_requests(params=json.dumps(token_name_rpc))
        else:
            response = [make_requests(params=json.dumps(token_name_rpc[0]))]

        for data in list(zip_rpc_response(tokens, response)):
            result = rpc_response_to_result(data[1])

            token = data[0]
            value = result[2:] if result is not None else None
            key = to_snake_case(fn_name)
            try:
                token[key] = abi.decode([token["data_type"]], bytes.fromhex(value))[0]
                if token["data_type"] == "string":
                    token[key] = token[fn_name].replace("\u0000", "")
            except Exception as e:
                logger.warning(
                    f"Decoding token {fn_name} failed. "
                    f"token: {token}. "
                    f"rpc response: {result}. "
                    f"exception: {e}"
                )
                exception_recorder.log(
                    block_number=token["block_number"],
                    dataclass=Token.type(),
                    message_type=f"decode_token_{fn_name}_fail",
                    message=str(e),
                    exception_env=token,
                    level=RecordLevel.WARN,
                )

                token[key] = None

    for token in tokens:
        if token["token_type"] != TokenType.ERC1155.value:
            if token.get("token_uri") is not None or token.get("owner_of") is not None or token.get("decimals") is None:
                token["token_type"] = TokenType.ERC721.value
            else:
                token["token_type"] = TokenType.ERC20.value

    return tokens
