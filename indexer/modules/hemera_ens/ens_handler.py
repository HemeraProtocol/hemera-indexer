#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/4/24 13:15
# @Author  will
# @File  ens_handler.py
# @Brief
import logging
from collections import defaultdict
from dataclasses import asdict
from multiprocessing import Queue

from eth_abi.codec import ABICodec
from web3 import Web3

from indexer.modules.hemera_ens import lifo_registry
from indexer.modules.hemera_ens.ens_abi import abi_map
from indexer.modules.hemera_ens.ens_conf import CONTRACT_NAME_MAP, ENS_CONTRACT_CREATED_BLOCK, REVERSE_BASE_NODE
from indexer.modules.hemera_ens.ens_domain import ENSAddressChangeD, ENSAddressD, ENSNameRenewD, ENSRegisterD, \
    ENSMiddleD
from indexer.modules.hemera_ens.ens_hash import namehash
from indexer.modules.hemera_ens.extractors import BaseExtractor, RegisterExtractor
from indexer.modules.hemera_ens.util import convert_str_ts

logger = logging.getLogger(__name__)


class EnsConfLoader:
    def __init__(self, provider=None):
        self.contract_object_map = None
        self.event_map = None
        self.function_map = None
        if not provider:
            provider = "https://ethereum-rpc.publicnode.com"
        self.w3 = Web3(Web3.HTTPProvider(provider))
        self.w3.codec = ABICodec(lifo_registry)
        self.build_contract_map()

    def build_contract_map(self):
        contract_object_map = {}
        for ad_lower in CONTRACT_NAME_MAP:
            if ad_lower not in abi_map:
                continue
            abi = abi_map[ad_lower]
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(ad_lower), abi=abi)
            contract_object_map[ad_lower] = contract

        event_map = defaultdict(dict)
        function_map = defaultdict(dict)

        for contract_address, contract in contract_object_map.items():
            abi_events = [abi for abi in contract.abi if abi["type"] == "event"]
            for event in abi_events:
                sig = self.get_signature_of_event(event)
                event_map[sig] = event
            functions = [abi for abi in contract.abi if abi["type"] == "function"]
            for function in functions:
                sig = self.get_function_signature(function)
                function_map["0x" + sig[0:8]] = function
        self.contract_object_map = contract_object_map
        self.event_map = event_map
        self.function_map = function_map

    def get_signature_of_event(self, event):
        name = event["name"]
        inputs = [p["type"] for p in event["inputs"]]
        inputs = ",".join(inputs)
        text = f"{name}({inputs})"
        sig = self.w3.to_hex(Web3.keccak(text=text))
        return sig

    def get_function_signature(self, function_abi):
        name = function_abi["name"]
        inputs = [input["type"] for input in function_abi["inputs"]]
        signature = f"{name}({','.join(inputs)})"
        keccak_hash = self.w3.keccak(text=signature)
        function_selector = keccak_hash
        function_selector_hex = function_selector.hex()
        return function_selector_hex


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class EnsHandler:
    def __init__(self, ens_conf_loader):
        self.rss = []
        self.result = Queue()
        self.ens_conf_loader = ens_conf_loader
        self.contract_object_map = self.ens_conf_loader.contract_object_map
        self.function_map = self.ens_conf_loader.function_map
        self.event_map = self.ens_conf_loader.event_map
        self.extractors = [extractor() for extractor in BaseExtractor.__subclasses__()]

    def is_ens_address(self, address):
        return address.lower() in self.ens_conf_loader.contract_object_map

    def get_event_name(self, sig):
        event = self.event_map[sig]
        if not event:
            logger.error("No Event sig: {}, event_map: {}".format(sig, self.event_map))
            raise ValueError(f"No event for {sig}")
        return event["name"]

    def get_function_name(self, sig):
        f = self.function_map[sig]
        if not f:
            logger.error("No function sig: {}, event_map: {}".format(sig, self.function_map))
            raise ValueError(f"No function sig: {sig}")
        return f["name"]

    def decode_transaction(self, transaction):
        if not transaction["to_address"]:
            return None
        con = self.contract_object_map[transaction["to_address"]]
        decoded_input = con.decode_function_input(transaction["input"])
        return decoded_input

    def process(self, transaction, logs):
        if (
            not self.is_ens_address(transaction["to_address"])
            or transaction["block_number"] < ENS_CONTRACT_CREATED_BLOCK
        ):
            return []
        method = None
        tra_sig = transaction["input"][0:10]
        if tra_sig in self.function_map:
            function = self.function_map[tra_sig]
            if function:
                method = function.get("name")
        tra = transaction
        dic = {
            "transaction_hash": tra["hash"],
            "log_index": None,
            "transaction_index": tra["transaction_index"],
            "block_number": tra["block_number"],
            "block_hash": tra["block_hash"],
            "block_timestamp": convert_str_ts(tra["block_timestamp"]),
            "method": method,
            "event_name": None,
            "from_address": tra["from_address"],
            "to_address": tra["to_address"],
            "name": None,
            "base_node": None,
            "node": None,
            "label": None,
            "expires": None,
            "owner": None,
            "resolver": None,
            "address": None,
            "reverse_node": None,
            "reverse_label": None,
            "reverse_name": None,
            "reverse_base_node": None,
        }
        # While, setName doesn't mean `nameChanged` occurs, just ignore it
        if method == 'setName':
            d_tnx = self.decode_transaction(transaction)
            ens_middle = AttrDict(dic)
            ens_middle.log_index = -1
            name = None
            if d_tnx[1].get('name'):
                name = d_tnx[1]['name']
            elif d_tnx[1].get('newName'):
                name = d_tnx[1]['newName']
            if not name or len(name) - 4 != name.find('.'):
                # 二级或者非法
                return []
            ens_middle.reverse_name = name

            ens_middle.node = namehash(name)
            ens_middle.address = tra['from_address'].lower()
            return [ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                reverse_name=ens_middle.reverse_name,
                address=ens_middle.address,
                node=ens_middle.node,
                reverse_node=None,
                reverse_base_node=REVERSE_BASE_NODE,
                event_name=None,
                method='setName',
            )]
        res = []
        start = 0
        for idx, single_log in enumerate(logs):
            if not self.is_ens_address(single_log["address"]):
                continue
            if not single_log.get("topic0") or (single_log["topic0"] not in self.event_map):
                continue
            single_log["address"] = single_log["address"].lower()
            ens_middle = AttrDict(dic)
            ens_middle.log_index = single_log["log_index"]

            for extractor in self.extractors:
                solved_event = extractor.extract(
                    single_log["address"],
                    single_log["topic0"],
                    single_log,
                    ens_middle,
                    self.contract_object_map,
                    self.event_map,
                    logs[start : idx + 1],
                )
                if solved_event:
                    res.append(solved_event)
                    if single_log["topic0"] == RegisterExtractor.tp0_register:
                        start = idx
                    break

        return res

    def process_middle(self, lis):
        if not lis:
            return []
        items = []
        for record in lis:
            dic = self.resolve_middle(asdict(record))
            items.append(dic)
        return items

    def resolve_middle(self, record):
        name = record.get("name")
        if name and not name.endswith(".eth"):
            name += ".eth"
        address = record.get("address")
        if address:
            address = address.lower()
        if record.get("expires"):
            if isinstance(record.get("expires"), str):
                record["expires"] = record.get("expires")
            else:
                record["expires"] = record.get("expires").strftime("%Y-%m-%d %H:%M:%S")
        else:
            record["expires"] = None

        event_name = record.get("event_name")
        if not event_name:
            return None
        if event_name == "NameChanged":
            return ENSAddressD(
                address=address,
                reverse_node=record["reverse_node"],
                name=record["reverse_name"],
                block_number=record["block_number"],
            )
        if event_name == "NameRegistered":
            return ENSRegisterD(
                node=record["node"],
                name=record["name"],
                expires=record["expires"],
                registration=record["block_timestamp"],
                label=record["label"],
                first_owned_by=record["owner"],
                base_node=record["base_node"],
                token_id=record["token_id"],
                w_token_id=record["w_token_id"],
            )

        if event_name == "NameRenewed":
            return ENSNameRenewD(
                node=record["node"],
                expires=record["expires"],
            )
        if event_name == "AddressChanged":
            return ENSAddressChangeD(
                node=record["node"],
                address=address,
            )
