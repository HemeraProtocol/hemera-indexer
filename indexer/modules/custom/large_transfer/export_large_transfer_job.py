#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 11:26
# @Author  will
# @File  export_ens_job.py
# @Brief
import logging
from collections import defaultdict
from typing import List

from sqlalchemy import and_

from common.utils.exception_control import FastShutdownError
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob
from indexer.modules.custom.large_transfer.domain.large_transfer_domain import LargeTransferAddressD, LargeTransferTransactionD
from indexer.modules.custom.large_transfer.models.large_transfer_address import LargeTransferAddress

logger = logging.getLogger(__name__)

ETH = 'ETH'
TC = 'transaction_count'


class LargeTransferJob(ExtensionJob):
    dependency_types = [Transaction, ERC20TokenTransfer]
    output_types = [LargeTransferAddressD, LargeTransferTransactionD]
    able_to_reorg = True


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self.limit_eth = self.user_defined_config.get("eth") * (10 ** 18)

        self.rules = self.user_defined_config.get("rules")

        if self.limit_eth is None or len(self.rules) == 0:
            raise FastShutdownError("LargeTransferJob limit config is empty")

        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])

        self.db_service = kwargs["config"].get("db_service")

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        token_transfers = self._data_buff.get(ERC20TokenTransfer.type(), [])
        transactions_map = {}
        group_data = defaultdict(list)
        for ta in transactions:
            transactions_map[ta.hash] = ta
            group_data[ta.hash] = []
        for tf in token_transfers:
            group_data[tf.transaction_hash].append(tf)
        block_number = max(tra.block_number for tra in transactions)
        res = []
        address_token_in = defaultdict(lambda: defaultdict(int))
        address_token_out = defaultdict(lambda: defaultdict(int))
        for tnx, tfs in group_data.items():
            tra = transactions_map.get(tnx)
            if tra.value > self.limit_eth:
                res.append(LargeTransferTransactionD(
                    transaction_hash=tra.hash,
                    transaction_index=tra.transaction_index,
                    from_address=tra.from_address,
                    to_address=tra.to_address,
                    value=tra.value,
                    transaction_type=tra.transaction_type,
                    input=tra.input,
                    method_id=tra.input,
                    nonce=tra.nonce,
                    block_hash=tra.block_hash,
                    block_number=tra.block_number,
                    block_timestamp=tra.block_timestamp,

                ))

                address_token_in[tra.to_address][ETH] += tra.value
                address_token_in[tra.to_address][TC] += 1
                address_token_out[tra.from_address][ETH] += tra.value
                address_token_out[tra.from_address][TC] += 1

            else:
                large_flag = False
                for tf in tfs:
                    for rule in self.rules:
                        if tf.token_address == rule["token_address"] and tf.value > (rule["limit"] * 10 ** 6):
                            large_flag = True
                            address_token_in[tf.to_address][tf.token_address] += tf.value
                            address_token_in[tf.to_address][TC] += 1
                            address_token_out[tf.from_address][tf.token_address] += tf.value
                            address_token_out[tf.from_address][TC] += 1
                            break

                if large_flag:
                    res.append(LargeTransferTransactionD(
                    transaction_hash=tra.hash,
                    transaction_index=tra.transaction_index,
                    from_address=tra.from_address,
                    to_address=tra.to_address,
                    value=tra.value,
                    transaction_type=tra.transaction_type,
                    input=tra.input,
                    method_id=tra.input,
                    nonce=tra.nonce,
                    block_hash=tra.block_hash,
                    block_number=tra.block_number,
                    block_timestamp=tra.block_timestamp,
                    ))
        # query exists
        address_lis = list(set(address_token_in.keys()) | set(address_token_out.keys()))
        token_lis = list(set(get_second_level_keys(address_token_in)) | set(get_second_level_keys(address_token_out)))
        exists_dic = get_exist_large_transfers(self.db_service, address_lis, token_lis)
        # update value
        lafs = []
        for ad, token_balance_dic in address_token_in.items():
            for tk, balance in token_balance_dic.items():
                k = build_k(ad, tk)
                if tk == TC:
                    if k in exists_dic:
                        exists_dic[k].transaction_count += balance
                    else:
                        exists_dic[k] = LargeTransferAddressD(
                            address=ad,
                            token_address=tk,
                            transaction_count=balance,
                            amount_in=0,
                            amount_out=0,
                            block_number=block_number
                        )
                else:
                    if k in exists_dic:
                        exists_dic[k].amount_in += balance
                    else:
                        exists_dic[k] = LargeTransferAddressD(
                            address=ad,
                            token_address=tk,
                            transaction_count=1,
                            amount_in=balance,
                            amount_out=0,
                            block_number=block_number
                        )

        for ad, token_balance_dic in address_token_out.items():
            for tk, balance in token_balance_dic.items():
                k = build_k(ad, tk)
                if tk == TC:
                    if k in exists_dic:
                        exists_dic[k].transaction_count += balance
                    else:
                        exists_dic[k] = LargeTransferAddressD(
                            address=ad,
                            token_address=tk,
                            transaction_count=balance,
                            amount_in=0,
                            amount_out=0,
                            block_number=block_number
                        )
                else:
                    if k in exists_dic:
                        exists_dic[k].amount_out += balance
                    else:
                        exists_dic[k] = LargeTransferAddressD(
                            address=ad,
                            token_address=tk,
                            transaction_count=1,
                            amount_in=0,
                            amount_out=balance,
                            block_number=block_number
                        )
        for item in res + list(exists_dic.values()):
            if item:
                self._collect_item(item.type(), item)

def get_second_level_keys(nested_dict):
    second_level_keys = set()
    for value in nested_dict.values():
        if isinstance(value, dict):
            second_level_keys.update(value.keys())
    return list(second_level_keys)


def get_exist_large_transfers(db_service, address_lis, token_address_lis):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(LargeTransferAddress).filter(and_(LargeTransferAddress.address.in_(address_lis), LargeTransferAddress.token_address.in_(token_address_lis))).all()
        )
        res = {}
        for row in result:
            res[build_k(row.address, row.token_address)] = LargeTransferAddressD(
                address=row.address,
                token_address=row.token_address,
                transaction_count=row.transaction_count,
                amount_in=row.amount_in,
                amount_out=row.amount_out,
                block_number=row.block_number
            )

    except Exception as e:
        raise e
    finally:
        session.close()

    return res

def build_k(address, token_address):
    return address + '.' + token_address
