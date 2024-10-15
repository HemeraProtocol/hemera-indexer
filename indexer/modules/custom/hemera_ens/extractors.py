#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/6/28 15:34
# @Author  will
# @File  extractors.py
# @Brief
import logging

from web3 import Web3

from common.utils.format_utils import hex_str_to_bytes
from indexer.modules.custom.hemera_ens.ens_conf import BASE_NODE, REVERSE_BASE_NODE
from indexer.modules.custom.hemera_ens.ens_domain import ENSMiddleD
from indexer.modules.custom.hemera_ens.ens_hash import compute_node_label, namehash
from indexer.modules.custom.hemera_ens.util import convert_str_ts

logger = logging.getLogger(__name__)


def decode_log(lg, contract_object_map, event_map):
    tp0 = lg["topic0"]
    con = contract_object_map[lg["address"]]

    matched_event = event_map.get(tp0)
    if not matched_event:
        return None
    try:
        topics = [hex_str_to_bytes(lg.get("topic" + str(i))) for i in range(4) if lg.get("topic" + str(i))]
        wlg = {
            "address": lg.get("address"),
            "topics": topics,
            "data": hex_str_to_bytes(lg.get("data")),
            "blockNumber": lg.get("block_number"),
            "transactionHash": lg.get("transaction_hash"),
            "transactionIndex": lg.get("transaction_index"),
            "blockHash": lg.get("block_hash"),
            "logIndex": lg.get("log_index"),
            "removed": False,
        }
        dl = con.events[matched_event["name"]]().process_log(wlg)
        event_data = {
            "args": dict(dl["args"]),
            "event": dl["event"],
            "logIndex": dl["logIndex"],
            "transactionIndex": dl["transactionIndex"],
            "transactionHash": dl["transactionHash"],
            "address": dl["address"],
            "blockHash": dl["blockHash"],
            "blockNumber": dl["blockNumber"],
            "_sig": lg["topic0"],
            "_event": matched_event["name"],
        }

        inputs = matched_event["inputs"]
        for ipt in inputs:
            k = ipt["name"]
            if k not in dl["args"]:
                continue
            v = dl["args"][k]
            if isinstance(v, bytes):
                v = Web3.to_hex(v).lower()
            event_data["args"][k] = v
    except Exception as e:
        logger.error("An exception occurred while processing log: {}, wlg: {}, e: {}".format(lg, wlg, e))
        return None
    else:
        return event_data


class BaseExtractor(object):
    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        pass


class RegisterExtractor(BaseExtractor):

    tp0_register = "0xca6abbe9d7f11422cb6ca7629fbf6fe9efb1c621f71ce8f02b9f2a230097404f"

    tp_register_with_token = "0xce0457fe73731f824cc272376169235128c118b49d344817417c6d108d155e82"

    def __init__(self):
        self.address = "0x283af0b28c62c092c9727f1ee09c02ca627eb7f5"

        self.address1 = "0x253553366da8546fc250f225fe3d25d0c782303b"
        self.tp0a = "0x69e37f151eb98a09618ddaa80c8cfaf1ce5996867c489f45b555b412271ebf27"

        self.address2 = "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85"
        self.tpb = "0xb3d987963d01b2f68493b4bdb130988f157ea43070d4ad840fee0466ed9370d9"

    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        if (tp0 == RegisterExtractor.tp0_register) or (tp0 == self.tp0a):
            event_data = decode_log(log, contract_object_map, event_map)
            tmp = event_data["args"]
            ens_middle.expires = convert_str_ts(tmp.get("expires", ""))
            ens_middle.name = tmp.get("name")
            if "." in ens_middle.name:
                # not supported
                return None
            ens_middle.name = ens_middle.name + ".eth"
            ens_middle.label = tmp.get("label").lower()
            ens_middle.owner = tmp.get("owner").lower()
            ens_middle.base_node = BASE_NODE
            ens_middle.node = namehash(ens_middle.name)
            ens_middle.event_name = event_data["_event"]
            token_id = None
            w_token_id = None
            for sl in prev_logs[::-1]:
                if (
                    sl["address"] == "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85"
                    and (sl["topic2"]) == log["topic2"]
                    and sl["topic0"] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    token_id = str(int(sl["topic3"], 16))
                if (
                    sl["address"] == "0xd4416b13d2b3a9abae7acd5d6c2bbdbe25686401"
                    and sl["topic0"] == "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
                ):
                    evd = decode_log(sl, contract_object_map, event_map)
                    if evd["args"].get("id"):
                        w_token_id = str(evd["args"].get("id"))
            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                topic0=tp0,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                expires=ens_middle.expires,
                name=ens_middle.name,
                label=ens_middle.label,
                owner=ens_middle.owner,
                base_node=ens_middle.base_node,
                node=ens_middle.node,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
                token_id=token_id,
                w_token_id=w_token_id,
            )
        elif address == self.address2 and tp0 == self.tpb:
            token_id = int(str(log["topic1"]).lower(), 16)
            owner = extract_eth_address(str(log["topic2"]).lower()[2:])
            event_data = decode_log(log, contract_object_map, event_map)
            ens_middle.event_name = event_data["_event"]

            node = None
            label = None
            base_node = None
            for sl in prev_logs[::-1]:
                if (
                    sl["address"] == "0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e"
                    and sl["topic0"] == RegisterExtractor.tp_register_with_token
                ):
                    base_node = sl["topic1"]
                    label = sl["topic2"]
                    node = compute_node_label(base_node, label)
                    break
                elif (
                    sl["address"] == "0x314159265dd8dbb310642f98f50c066173c1259b"
                    and sl["topic0"] == "0xce0457fe73731f824cc272376169235128c118b49d344817417c6d108d155e82"
                ):
                    base_node = sl["topic1"]
                    label = sl["topic2"]
                    node = compute_node_label(base_node, label)
                    break
            if not node:
                return None

            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                topic0=tp0,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                expires=ens_middle.expires,
                name=ens_middle.name,
                base_node=base_node,
                label=label,
                owner=owner,
                node=node,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
                token_id=token_id,
            )
        else:
            return None


class AncientRegister(BaseExtractor):

    def __init__(self):
        self.address = "0x6090a6e47849629b7245dfa1ca21d94cd15878ef"
        self.tp0 = "0x0f0c27adfd84b60b6f456b0e87cdccb1e5fb9603991588d87fa99f5b6b61e670"

    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        if tp0 == self.tp0:
            event_data = decode_log(log, contract_object_map, event_map)
            tmp = event_data["args"]
            ens_middle.expires = convert_str_ts(tmp.get("expires", ""))

            ens_middle.label = log["topic1"]
            ens_middle.owner = extract_eth_address(log["topic2"])
            ens_middle.base_node = BASE_NODE
            ens_middle.node = compute_node_label(BASE_NODE, ens_middle.label)
            ens_middle.event_name = event_data["_event"]
            token_id = str(int(log["topic1"], 16))
            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                topic0=tp0,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                expires=ens_middle.expires,
                name=ens_middle.name,
                label=ens_middle.label,
                owner=ens_middle.owner,
                base_node=ens_middle.base_node,
                node=ens_middle.node,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
                token_id=token_id,
                w_token_id=None,
            )


class NameRenewExtractor(BaseExtractor):
    def __init__(self):
        self.address = "0x253553366da8546fc250f225fe3d25d0c782303b"
        self.tp0 = "0x3da24c024582931cfaf8267d8ed24d13a82a8068d5bd337d30ec45cea4e506ae"
        self.address1 = "0x283af0b28c62c092c9727f1ee09c02ca627eb7f5"

    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        if tp0 == self.tp0:
            event_data = decode_log(log, contract_object_map, event_map)

            tmp = event_data["args"]
            name = tmp.get("name")
            if "." in name:
                return None
            name = name + ".eth"
            ens_middle.name = name
            ens_middle.node = namehash(name)
            ens_middle.label = tmp.get("label").lower()
            ens_middle.expires = convert_str_ts(tmp.get("expires", ""))
            ens_middle.event_name = event_data["_event"]

            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                topic0=tp0,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                name=ens_middle.name,
                node=ens_middle.node,
                label=ens_middle.label,
                expires=ens_middle.expires,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
            )


class AddressChangedExtractor(BaseExtractor):
    def __init__(self):
        self.address = "0x231b0ee14048e9dccd1d247744d114a4eb5e8e63"
        self.address1 = "0x226159d592e2b063810a10ebf6dcbada94ed68b8"
        self.tp0 = "0x65412581168e88a1e60c6459d7f44ae83ad0832e670826c05a4e2476b57af752"

    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        if tp0 == self.tp0:
            event_data = decode_log(log, contract_object_map, event_map)
            tmp = event_data["args"]
            coin_type = tmp["coinType"]
            if not coin_type or str(coin_type) != "60":
                return None
            ens_middle.node = tmp["node"]
            ens_middle.address = tmp["newAddress"].lower()
            ens_middle.event_name = event_data["_event"]
            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                topic0=tp0,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                node=ens_middle.node,
                address=ens_middle.address,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
            )

        return None


class NameChangedExtractor(BaseExtractor):
    def __init__(self):
        self.address = "0x231b0ee14048e9dccd1d247744d114a4eb5e8e63"
        self.tp0 = "0xb7d29e911041e8d9b843369e890bcb72c9388692ba48b65ac54e7214c4c348f7"

    def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSMiddleD:
        if tp0 == self.tp0:
            event_data = decode_log(log, contract_object_map, event_map)
            tmp = event_data["args"]
            name = tmp.get("name") or ""
            if not name or len(name) - 4 != name.find("."):
                # 二级或者非法
                return None
            ens_middle.reverse_name = name
            ens_middle.address = ens_middle.from_address
            ens_middle.node = namehash(name)
            ens_middle.reverse_base_node = REVERSE_BASE_NODE
            ens_middle.reverse_node = str(log["topic1"]).lower()
            ens_middle.event_name = event_data["_event"]
            return ENSMiddleD(
                transaction_hash=ens_middle.transaction_hash,
                log_index=ens_middle.log_index,
                transaction_index=ens_middle.transaction_index,
                block_number=ens_middle.block_number,
                block_hash=ens_middle.block_hash,
                block_timestamp=ens_middle.block_timestamp,
                topic0=tp0,
                from_address=ens_middle.from_address,
                to_address=ens_middle.to_address,
                reverse_name=ens_middle.reverse_name,
                address=ens_middle.address,
                node=ens_middle.node,
                reverse_node=ens_middle.reverse_node,
                reverse_base_node=REVERSE_BASE_NODE,
                event_name=ens_middle.event_name,
                method=ens_middle.method,
            )


"""
** integrate with ERC1155 & ERC721 transactions **
"""
# class TransferExtractor(BaseExtractor):
#     def __init__(self):
#         self.address = "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85"
#         self.tp0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
#
#     def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSTokenTransferD:
#         if address == self.address and tp0 == self.tp0:
#             return ENSTokenTransferD(
#                 transaction_hash=ens_middle.transaction_hash,
#                 log_index=ens_middle.log_index,
#                 from_address=log['topic1'],
#                 to_address=log['topic2'],
#                 token_id=(int(log['topic3'], 16)),
#                 token_type='ERC721',
#                 token_address=log['address'],
#                 block_number=ens_middle.block_number,
#                 block_hash=ens_middle.block_hash,
#                 block_timestamp=ens_middle.block_timestamp,
#             )
#
# class TransferSingle(BaseExtractor):
#     def __init__(self):
#         self.address = '0xd4416b13d2b3a9abae7acd5d6c2bbdbe25686401'
#         self.tp0 = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
#
#     def extract(self, address, tp0, log, ens_middle, contract_object_map, event_map, prev_logs=None) -> ENSTokenTransferD:
#         if address == self.address and tp0 == self.tp0:
#             event_data = decode_log(log, contract_object_map, event_map)
#             return ENSTokenTransferD(
#                 transaction_hash=ens_middle.transaction_hash,
#                 log_index=ens_middle.log_index,
#                 from_address=log['topic2'],
#                 to_address=log['topic3'],
#                 token_id=event_data["args"].get("id"),
#                 token_type='ERC1155',
#                 token_address=log['address'],
#                 block_number=ens_middle.block_number,
#                 block_hash=ens_middle.block_hash,
#                 block_timestamp=ens_middle.block_timestamp,
#             )


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()
