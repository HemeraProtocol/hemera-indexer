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
from indexer.modules.hemera_ens.ens_conf import CONTRACT_NAME_MAP
from indexer.modules.hemera_ens.ens_domain import ENSRel
from indexer.modules.hemera_ens.extractors import (
    AddressChangedExtractor,
    NameChangedExtractor,
    NameRenewExtractor,
    RegisterExtractor,
)
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
                function_map[sig[0:10]] = function
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
        self.extractors = [RegisterExtractor(), NameRenewExtractor(), AddressChangedExtractor(), NameChangedExtractor()]

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
        if not self.is_ens_address(transaction["to_address"]):
            return []
        tra = transaction
        dic = {
            "type": "ens_middle",
            "transaction_hash": tra["hash"],
            "log_index": None,
            "block_number": tra["block_number"],
            "block_hash": tra["block_hash"],
            "block_timestamp": convert_str_ts(tra["block_timestamp"]),
            "method": None,
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
        # while setName doesn't mean nameChanged occurs, just ignore it
        # if method == 'setName':

        res = []
        for single_log in logs:
            if not self.is_ens_address(single_log["address"]):
                continue
            if not single_log["topic0"] or (single_log["topic0"] not in self.event_map):
                continue
            tp0 = single_log["topic0"]
            address = single_log["address"].lower()
            single_log["address"] = address
            ens_middle = AttrDict(dic)
            ens_middle.log_index = single_log["log_index"]

            for extractor in self.extractors:
                solved_event = extractor.extract(
                    address, tp0, single_log, ens_middle, self.contract_object_map, self.event_map
                )
                if solved_event:
                    res.append(solved_event)
                    break

        return res

    def process_middle(self, lis):
        if not lis:
            return
        items = []
        for record in lis:
            dic = self.resolve_dict_to_item(asdict(record))
            items.append(dic)
        return items

    def resolve_dict_to_item(self, record):
        name = record.get("name")
        if name and not name.endswith(".eth"):
            name += ".eth"
        address = record.get("address")
        if address:
            address = address.lower()
        dic = {
            "node": record.get("node"),
            "owner": record.get("owner"),
            "address": address,
            "name": name,
            "reverse_name": record.get("reverse_name"),
        }
        if record.get("expires"):
            if isinstance(record.get("expires"), str):
                dic["expires"] = record.get("expires")
            else:
                dic["expires"] = record.get("expires").strftime("%Y-%m-%d %H:%M:%S")
        else:
            dic["expires"] = None
        return ENSRel(
            node=dic.get("node"),
            token_id=dic.get("token_id"),
            name=dic.get("name"),
            owner=dic.get("owner"),
            expires=dic.get("expires"),
            address=dic.get("address"),
            reverse_name=dic.get("reverse_name"),
        )
