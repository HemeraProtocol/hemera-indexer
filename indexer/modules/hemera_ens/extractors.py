#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/6/28 15:34
# @Author  will
# @File  extractors.py
# @Brief
from typing import cast
import orjson
from eth_typing import ABIEvent

from indexer.modules.hemera_ens.ens_conf import BASE_NODE, REVERSE_BASE_NODE, CONTRACT_NAME_MAP
from indexer.modules.hemera_ens.ens_hash import namehash
from indexer.modules.hemera_ens.util import convert_str_ts
from indexer.domain.ens_model import ENSRegister, ENSNameRenew, ENSAddressChange, ENSNameChanged
from indexer.modules.bridge.signature import decode_log, event_log_abi_to_topic, function_abi_to_4byte_selector_str


class BaseExtractor(object):
    def extract(self, txn, ud_log):
        pass


class RegisterExtractor(BaseExtractor):
    def __init__(self):
        name_register_1 = cast(ABIEvent, orjson.loads("""{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"name","type":"string"},{"indexed":true,"internalType":"bytes32","name":"label","type":"bytes32"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"cost","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRegistered","type":"event"}"""))
        name_register_1_topic = event_log_abi_to_topic(name_register_1)
        NameRegistered2 = cast(ABIEvent, orjson.loads("""{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRegistered","type":"event"}"""))
        NameRegistered3 = cast(ABIEvent, orjson.loads("""{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"name","type":"string"},{"indexed":true,"internalType":"bytes32","name":"label","type":"bytes32"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"baseCost","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"premium","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRegistered","type":"event"}"""))
        self.address = '0x283af0b28c62c092c9727f1ee09c02ca627eb7f5'
        self.tp0 = '0xca6abbe9d7f11422cb6ca7629fbf6fe9efb1c621f71ce8f02b9f2a230097404f'

        self.address1 = '0x253553366da8546fc250f225fe3d25d0c782303b'
        self.tp0a = '0x69e37f151eb98a09618ddaa80c8cfaf1ce5996867c489f45b555b412271ebf27'

    def extract(self, txn, ud_log) -> ENSRegister:
        if (tp0 == self.tp0) or (tp0 == self.tp0a):
            event_data = ens_event.decode_log(log)
            tmp = event_data['args']
            ens_middle.expires = convert_str_ts(tmp.get('expires', ''))
            ens_middle.name = tmp.get('name')
            if '.' in ens_middle.name:
                # not supported
                return None
            ens_middle.label = tmp.get('label').lower()
            ens_middle.owner = tmp.get('owner').lower()
            ens_middle.base_node = BASE_NODE
            ens_middle.node = namehash(ens_middle.name + ".eth")
            ens_middle.event_name = event_data['_event']
            return ens_middle
        else:
            return None


class NameRenewExtractor(BaseExtractor):
    def __init__(self):
        self.address = '0x253553366da8546fc250f225fe3d25d0c782303b'
        self.tp0 = '0x3da24c024582931cfaf8267d8ed24d13a82a8068d5bd337d30ec45cea4e506ae'
        self.address1 = '0x283af0b28c62c092c9727f1ee09c02ca627eb7f5'

    def extract(self, txn, ud_log) -> ENSNameRenew:
        if tp0 == self.tp0:
            event_data = ens_event.decode_log(log)
            tmp = event_data['args']
            name = tmp.get('name')
            if '.' in name:
                return None
            ens_middle.name = name
            ens_middle.node = namehash(name + '.eth')
            ens_middle.label = tmp.get('label').lower()
            ens_middle.expires = convert_str_ts(tmp.get('expires', ''))
            ens_middle.event_name = event_data['_event']

            return ens_middle


class AddressChangedExtractor(BaseExtractor):
    def __init__(self):
        self.address = '0x231b0ee14048e9dccd1d247744d114a4eb5e8e63'
        self.address1 = '0x226159d592e2b063810a10ebf6dcbada94ed68b8'
        self.tp0 = '0x65412581168e88a1e60c6459d7f44ae83ad0832e670826c05a4e2476b57af752'

    def extract(self, txn, ud_log) -> ENSAddressChange:
        if tp0 == self.tp0:
            event_data = ens_event.decode_log(log)
            tmp = event_data['args']
            coin_type = tmp["coinType"]
            if not coin_type or str(coin_type) != '60':
                return None
            ens_middle.node = tmp['node']
            ens_middle.address = tmp['newAddress'].lower()
            ens_middle.event_name = event_data['_event']
            return ens_middle

        return None


class NameChangedExtractor(BaseExtractor):
    def __init__(self):
        self.address = '0x231b0ee14048e9dccd1d247744d114a4eb5e8e63'
        self.tp0 = '0xb7d29e911041e8d9b843369e890bcb72c9388692ba48b65ac54e7214c4c348f7'

    def extract(self, txn, ud_log) -> ENSNameChanged:
        if tp0 == self.tp0:
            event_data = ens_event.decode_log(log)
            tmp = event_data['args']
            name = tmp.get('name') or ''
            if not name or len(name) - 4 != name.find('.'):
                # 二级或者非法
                return None
            ens_middle.reverse_name = name
            ens_middle.address = ens_middle.from_address
            ens_middle.node = namehash(name)
            ens_middle.reverse_node = REVERSE_BASE_NODE
            ens_middle.event_name = event_data['_event']
            return ens_middle
