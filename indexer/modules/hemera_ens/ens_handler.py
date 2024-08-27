#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/4/24 13:15
# @Author  will
# @File  ens_handler.py
# @Brief
import logging
from multiprocessing import Queue

from indexer.modules.hemera_ens.extractors import RegisterExtractor, AddressChangedExtractor, NameRenewExtractor, \
    NameChangedExtractor
from indexer.modules.hemera_ens.util import convert_str_ts
from indexer.modules.hemera_ens.ens_conf import CONTRACT_NAME_MAP

logger = logging.getLogger(__name__)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class EnsHandler:
    def __init__(self):
        self.rss = []
        self.result = Queue()
        self.extractors = [RegisterExtractor(), NameRenewExtractor(), AddressChangedExtractor(), NameChangedExtractor()]
        self.contract_name_map = CONTRACT_NAME_MAP

    def is_ens_address(self, address):
        return address.lower() in self.contract_name_map

    def process(self, transaction, logs):
        if not self.is_ens_address(transaction['to_address']):
            return []
        tra = transaction
        dic = {
            "type": "ens_middle",
            "transaction_hash": tra['hash'],
            "log_index": None,
            "block_number": tra['block_number'],
            "block_hash": tra['block_hash'],
            "block_timestamp": convert_str_ts(tra['block_timestamp']),
            'method': None,
            'event_name': None,
            "from_address": tra['from_address'],
            "to_address": tra['to_address'],
            "name": None,
            "base_node": None,
            "node": None,
            "label": None,
            "expires": None,
            "owner": None,
            "resolver": None,
            "address": None,
            'reverse_node': None,
            'reverse_label': None,
            'reverse_name': None,
            'reverse_base_node': None,
        }
        # while setName doesn't mean nameChanged occurs, just ignore it
        # if method == 'setName':
        #     d_tnx = self.decode_transaction(transaction)
        #     ens_middle = AttrDict(dic)
        #     ens_middle.log_index = -1
        #     name = None
        #     if d_tnx[1].get('name'):
        #         name = d_tnx[1]['name']
        #     elif d_tnx[1].get('newName'):
        #         name = d_tnx[1]['newName']
        #     if not name or len(name) - 4 != name.find('.'):
        #         # 二级或者非法
        #         return []
        #     ens_middle.reverse_name = name
        #
        #     ens_middle.node = namehash(name)
        #     ens_middle.address = tra['from_address'].lower()
        #     return [ens_middle]
        res = []
        for single_log in logs:
            if not self.is_ens_address(single_log['address']):
                continue
            if not single_log['topics'] or (single_log['topics'] and single_log['topics'][0] not in self.event_map):
                continue
            tp0 = single_log['topics'][0]
            address = single_log['address'].lower()
            single_log['address'] = address
            ens_middle = AttrDict(dic)
            ens_middle.log_index = single_log['log_index']

            for extractor in self.extractors:
                solved_event = extractor.extract(address, tp0, single_log, ens_middle, self.ens_event)
                if solved_event:
                    res.append(solved_event)
                    break

        return res

    def process_items(self, lis):
        if not lis:
            return
        items = []
        for record in lis:
            dic = self.resolve_dict_to_item(record)
            items.append(dic)
        return items

    def resolve_dict_to_item(self, record):
        name = record.get('name')
        if name and not name.endswith('.eth'):
            name += '.eth'
        address = record.get('address')
        if address:
            address = address.lower()
        dic = {
            'node': record.get('node'),
            'owner': record.get('owner'),
            'address': address,
            'name': name,
            'reverse_name': record.get('reverse_name'),
        }
        if record.get('expires'):
            if isinstance(record.get('expires'), str):
                dic['expires'] = record.get('expires')
            else:
                dic['expires'] = record.get('expires').strftime('%Y-%m-%d %H:%M:%S')
        else:
            dic['expires'] = None
        return dic
