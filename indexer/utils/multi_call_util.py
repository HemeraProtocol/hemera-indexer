#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/7 13:44
# @Author  will
# @File  multi_call_util.py
# @Brief aggregate many calls into one or several
import collections
import json
import logging

from eth_abi import abi
from multicall import Call, Multicall

from enumeration.record_level import RecordLevel
from indexer.domain.token_balance import TokenBalance
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.network_util import Network
from indexer.utils.utils import zip_rpc_response, rpc_response_to_result

exception_recorder = ExceptionRecorder()


class MultiCallUtil:

    def __init__(self, provider, logger=None):
        self.provider = provider
        if not logger:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
        self.multi = Multicall([], _w3=self.provider)
        self.net = Network.from_value(self.multi.chainid)
        self.deploy_block_number = self.net.deploy_block_number
        self.chunk_size = 1000

    def process(self, make_requests, raw_parameters, is_batch):
        token_balances = []
        result = {}
        grouped_data = collections.defaultdict(list)
        for item in raw_parameters:
            grouped_data[item['block_number']].append(item)
            token_balances.append({
                    "address": item["address"].lower(),
                    "token_id": item["token_id"],
                    "token_type": item["token_type"],
                    "token_address": item["token_address"].lower(),
                    "balance": None,
                    "block_number": item["block_number"],
                    "block_timestamp": item["block_timestamp"],
                }
            )
        for block_id, items in grouped_data.items():
            if block_id < self.deploy_block_number:
                # eth call
                self.logger.info(f'{block_id} < {self.deploy_block_number}, multicall not deployed, do eth_call')
                tmp = self.token_balances_rpc_requests(make_requests, items, is_batch)
                result.update(tmp)
            else:
                # try multicall
                chunks = self.chunk_list(items, self.chunk_size)
                for chunk in chunks:
                    try:
                        tm = self.process_chunk(chunk, block_id)

                        result.update(tm)
                    except Exception as e:
                        # eth call
                        self.logger.warning(f"Exception while processing block {block_id}: {e}, downgrade to eth_call")
                        tmp = self.token_balances_rpc_requests(make_requests, items, is_batch)
                        result.update(tmp)
        for itt in token_balances:
            bk = self.build_key(itt)
            if bk in result:
                itt['balance'] = result[bk]
        return token_balances

    @staticmethod
    def build_key(dic):
        return '_'.join([dic['address'], dic['token_address'], str(dic['block_number']), dic['token_type'],
                         str(dic['token_id'])])

    @staticmethod
    def chunk_list(lst, chunk_size):
        """将列表分割成指定大小的块"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    def process_chunk(self, chunk, block_id):
        calls = []
        tm = {}
        for row in chunk:
            token, wal = row['token_address'], row['address']
            token_id = row['token_id']
            if token_id:
                calls.append(Call(token, ['balanceOf(address,uint256)(uint256)', wal, token_id], [(self.build_key(row), None)]))
            else:
                calls.append(Call(token, ['balanceOf(address)(uint256)', wal], [(self.build_key(row), None)]))
        self.multi.calls = calls
        self.multi.block_id = block_id

        result = self.multi()
        if result:
            tm.update(result)
        return result

    def token_balances_rpc_requests(self, make_requests, tokens, is_batch):
        result_dic = {}
        for idx, token in enumerate(tokens):
            token["request_id"] = idx

        token_balance_rpc = list(generate_eth_call_json_rpc(tokens))

        if is_batch:
            response = make_requests(params=json.dumps(token_balance_rpc))
        else:
            response = [make_requests(params=json.dumps(token_balance_rpc[0]))]

        for data in list(zip_rpc_response(tokens, response)):
            result = rpc_response_to_result(data[1])
            balance = None

            try:
                if result:
                    balance = abi.decode(["uint256"], bytes.fromhex(result[2:]))[0]
                    result_dic[self.build_key(data[0])] = balance

            except Exception as e:
                self.logger.warning(
                    f"Decoding token balance value failed. "
                    f"token address: {data[0]['token_address']}. "
                    f"rpc response: {result}. "
                    f"block number: {data[0]['block_number']}. "
                    f"exception: {e}. "
                )
                exception_recorder.log(
                    block_number=data[0]["block_number"],
                    dataclass=TokenBalance.type(),
                    message_type="DecodeTokenBalanceFail",
                    message=str(e),
                    level=RecordLevel.WARN,
                )

        return result_dic
