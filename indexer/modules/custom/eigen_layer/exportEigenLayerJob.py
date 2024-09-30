#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:07
# @Author  will
# @File  exportEigenLayerJob.py
# @Brief
import logging
from collections import defaultdict
from typing import Any, Dict, List

from eth_abi import decode
from eth_typing import Decodable
from sqlalchemy import func

from common.utils.exception_control import FastShutdownError
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.eigen_layer.eigen_layer_abi import (
    DEPOSIT_EVENT,
    SHARE_WITHDRAW_QUEUED,
    WITHDRAWAL_COMPLETED_EVENT,
    WITHDRAWAL_QUEUED_EVENT,
    WITHDRAWAL_QUEUED_EVENT_2,
)
from indexer.modules.custom.eigen_layer.eigen_layer_conf import CHAIN_CONTRACT
from indexer.modules.custom.eigen_layer.eigen_layer_domain import (
    EigenLayerActionD,
    EigenLayerAddressCurrentD,
    eigen_layer_address_current_factory,
)
from indexer.modules.custom.eigen_layer.models.af_eigen_layer_address_current import AfEigenLayerAddressCurrent
from indexer.modules.custom.eigen_layer.models.af_eigen_layer_records import AfEigenLayerRecords
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import bytes_to_hex_str, decode_log

logger = logging.getLogger(__name__)


class ExportEigenLayerJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [EigenLayerActionD, EigenLayerAddressCurrentD]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self.db_service = kwargs["config"].get("db_service")
        self.chain_id = self._web3.eth.chain_id
        self.eigen_layer_conf = CHAIN_CONTRACT[self.chain_id]

    def get_filter(self):
        # deposit, startWithdraw, finishWithdraw
        topics = []
        addresses = []
        for k, item in self.eigen_layer_conf.items():
            topics.append(item["topic"])
            addresses.append(item["address"])

        return [
            TransactionFilterByLogs(topics_filters=[TopicSpecification(topics=topics, addresses=addresses)]),
        ]

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        res = []

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if (
                    log.topic0 == self.eigen_layer_conf["DEPOSIT"]["topic"]
                    and log.address == self.eigen_layer_conf["DEPOSIT"]["address"]
                ):
                    dl = decode_log(DEPOSIT_EVENT, log)
                    staker = dl.get("staker")
                    token = dl.get("token")
                    strategy = dl.get("strategy")
                    shares = dl.get("shares")

                    kad = EigenLayerActionD(
                        transaction_hash=transaction.hash,
                        log_index=log.log_index,
                        transaction_index=transaction.transaction_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        method=transaction.get_method_id(),
                        event_name=DEPOSIT_EVENT["name"],
                        topic0=log.topic0,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        strategy=strategy,
                        token=token,
                        shares=shares,
                        staker=staker,
                    )
                    res.append(kad)
                elif (
                    log.topic0 == self.eigen_layer_conf["START_WITHDRAW"]["topic"]
                    and log.address == self.eigen_layer_conf["START_WITHDRAW"]["address"]
                ):
                    dl = decode_log(WITHDRAWAL_QUEUED_EVENT, log)

                    withdrawal_root = dl.get("withdrawalRoot")
                    withdrawal_struct = dl.get("withdrawal")

                    staker = withdrawal_struct.get("staker")
                    withdrawer = withdrawal_struct.get("withdrawer")
                    shares_lis = withdrawal_struct.get("shares")
                    strategy_lis = withdrawal_struct.get("strategies")
                    if len(shares_lis) != len(strategy_lis):
                        raise FastShutdownError(f"eigen_layer_job error data tnx {transaction.hash}")
                    for idx in range(len(strategy_lis)):
                        strategy = strategy_lis[idx]
                        shares = shares_lis[idx]
                        kad = EigenLayerActionD(
                            transaction_hash=transaction.hash,
                            log_index=log.log_index,
                            internal_idx=idx,
                            transaction_index=transaction.transaction_index,
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            method=transaction.get_method_id(),
                            event_name=WITHDRAWAL_QUEUED_EVENT["name"],
                            topic0=log.topic0,
                            from_address=transaction.from_address,
                            to_address=transaction.to_address,
                            strategy=strategy,
                            staker=staker,
                            withdrawer=withdrawer,
                            shares=shares,
                            withdrawroot=withdrawal_root,
                        )
                        res.append(kad)
                elif (
                    log.topic0 == self.eigen_layer_conf["START_WITHDRAW_2"]["topic"]
                    and log.address == self.eigen_layer_conf["START_WITHDRAW_2"]["address"]
                ):
                    dl = decode_log(WITHDRAWAL_QUEUED_EVENT_2, log)

                    withdrawal_root = dl.get("withdrawalRoot")

                    staker = dl.get("depositor")
                    withdrawer = dl.get("withdrawer")
                    nonce = dl.get("nonce")
                    internal_idx = 0
                    for lg in logs:
                        if lg.topic0 == self.eigen_layer_conf["START_WITHDRAW_2"]["prev_topic"]:
                            dl2 = decode_log(SHARE_WITHDRAW_QUEUED, lg)
                            dl2_nonce = dl2.get("nonce")
                            if dl2_nonce == nonce:
                                shares = dl2.get("shares")
                                strategy = dl2.get("strategy")

                                kad = EigenLayerActionD(
                                    transaction_hash=transaction.hash,
                                    log_index=log.log_index,
                                    internal_idx=internal_idx,
                                    transaction_index=transaction.transaction_index,
                                    block_number=log.block_number,
                                    block_timestamp=log.block_timestamp,
                                    method=transaction.get_method_id(),
                                    event_name=WITHDRAWAL_QUEUED_EVENT_2["name"],
                                    topic0=log.topic0,
                                    from_address=transaction.from_address,
                                    to_address=transaction.to_address,
                                    strategy=strategy,
                                    staker=staker,
                                    withdrawer=withdrawer,
                                    shares=shares,
                                    withdrawroot=withdrawal_root,
                                )
                                internal_idx += 1
                                res.append(kad)
                elif (
                    log.topic0 == self.eigen_layer_conf["FINISH_WITHDRAW"]["topic"]
                    and log.address == self.eigen_layer_conf["FINISH_WITHDRAW"]["address"]
                ):
                    dl = decode_log(WITHDRAWAL_COMPLETED_EVENT, log)
                    withdrawal_root = dl.get("withdrawalRoot")
                    res.append(
                        EigenLayerActionD(
                            transaction_hash=transaction.hash,
                            log_index=log.log_index,
                            transaction_index=transaction.transaction_index,
                            internal_idx=0,
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            method=transaction.get_method_id(),
                            event_name=WITHDRAWAL_COMPLETED_EVENT["name"],
                            topic0=log.topic0,
                            from_address=transaction.from_address,
                            to_address=transaction.to_address,
                            staker=None,
                            withdrawer=None,
                            shares=None,
                            strategy=None,
                            token=None,
                            withdrawroot=withdrawal_root,
                        )
                    )
                    # try:
                    #     df = decode_transaction_data(FINISH_WITHDRAWAL_FUNCTION, HexStr(transaction.input))
                    # except Exception as e:
                    #     # when input is not able to decoded
                    #     res.append(
                    #         EigenLayerActionD(
                    #             transaction_hash=transaction.hash,
                    #             log_index=log.log_index,
                    #             transaction_index=transaction.transaction_index,
                    #             internal_idx=0,
                    #             block_number=log.block_number,
                    #             block_timestamp=log.block_timestamp,
                    #             method=transaction.get_method_id(),
                    #             event_name=WITHDRAWAL_COMPLETED_EVENT["name"],
                    #             topic0=log.topic0,
                    #             from_address=transaction.from_address,
                    #             to_address=transaction.to_address,
                    #             staker=None,
                    #             withdrawer=None,
                    #             shares=None,
                    #             strategy=None,
                    #             token=None,
                    #             withdrawroot=withdrawal_root,
                    #         )
                    #     )
                    #
                    #     df = {"withdrawals": []}
                    # withdrawal_struct_lis = df.get("withdrawals")
                    # base_multiplier = 1000000
                    # for outer_idx, withdrawal_struct in enumerate(withdrawal_struct_lis):
                    #     staker = withdrawal_struct.get("staker")
                    #     withdrawer = withdrawal_struct.get("withdrawer")
                    #     strategy_lis = withdrawal_struct.get("strategies")
                    #     shares_lis = withdrawal_struct.get("shares")
                    #     if len(strategy_lis) != len(shares_lis):
                    #         raise FastShutdownError(f"eigen_layer_job error data tnx {transaction.hash}")
                    #     for idx in range(len(strategy_lis)):
                    #         strategy = strategy_lis[idx]
                    #         shares = shares_lis[idx]
                    #         internal_idx = outer_idx * base_multiplier + idx
                    #         kad = EigenLayerActionD(
                    #             transaction_hash=transaction.hash,
                    #             log_index=log.log_index,
                    #             transaction_index=transaction.transaction_index,
                    #             internal_idx=internal_idx,
                    #             block_number=log.block_number,
                    #             block_timestamp=log.block_timestamp,
                    #             method=transaction.get_method_id(),
                    #             event_name=FINISH_WITHDRAWAL_FUNCTION["name"],
                    #             topic0=log.topic0,
                    #             from_address=transaction.from_address,
                    #             to_address=transaction.to_address,
                    #             staker=staker,
                    #             withdrawer=withdrawer,
                    #             shares=shares,
                    #             strategy=strategy,
                    #             token=None,
                    #             withdrawroot=withdrawal_root,
                    #         )
                    #         res.append(kad)
        self.enrich_complete_withdraw(res)
        for item in res:
            self._collect_item(item.type(), item)
        batch_result_dic = self.calculate_batch_result(res)
        exists_dic = self.get_existing_address_current(list(batch_result_dic.keys()))
        for address, outer_dic in batch_result_dic.items():
            for vault, kad in outer_dic.items():
                if address in exists_dic and vault in exists_dic[address]:
                    exists_kad = exists_dic[address][vault]
                    exists_kad.deposit_amount += kad.deposit_amount
                    exists_kad.start_withdraw_amount += kad.start_withdraw_amount
                    exists_kad.finish_withdraw_amount += kad.finish_withdraw_amount
                    self._collect_item(kad.type(), exists_kad)
                else:
                    self._collect_item(kad.type(), kad)
        print("ok")

    @staticmethod
    def decode_function(decode_types, output: Decodable) -> Any:
        try:
            return decode(decode_types, output)
        except Exception as e:
            logger.error(e)
            return [None] * len(decode_types)

    def get_existing_address_current(self, addresses):
        if not self.db_service:
            return {}

        addresses = [ad[2:] for ad in addresses if ad and ad.startswith("0x")]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            query = session.query(AfEigenLayerAddressCurrent).filter(
                func.encode(AfEigenLayerAddressCurrent.address, "hex").in_(addresses)
            )
            result = query.all()
        lis = []
        for rr in result:
            lis.append(
                EigenLayerAddressCurrentD(
                    address=bytes_to_hex_str(rr.address),
                    strategy=bytes_to_hex_str(rr.strategy),
                    token=bytes_to_hex_str(rr.token) if rr.token else None,
                    deposit_amount=rr.deposit_amount,
                    start_withdraw_amount=rr.start_withdraw_amount,
                    finish_withdraw_amount=rr.finish_withdraw_amount,
                )
            )

        return create_nested_dict(lis)

    def enrich_complete_withdraw(self, actions: List[EigenLayerActionD]):
        roots = [action.withdrawroot for action in actions if action.event_name == WITHDRAWAL_COMPLETED_EVENT["name"]]
        ac_map = dict()
        with self.db_service.get_service_session() as session:
            query = session.query(AfEigenLayerRecords).filter(
                # func.encode(AfEigenLayerRecords.withdrawroot, "hex").in_(roots)
                (AfEigenLayerRecords.withdrawroot).in_(roots)
            )
            result = query.all()
            for rr in result:
                ac_map[rr.withdrawroot] = rr
        for action in actions:
            if action.event_name == WITHDRAWAL_COMPLETED_EVENT["name"]:
                st = ac_map[action.withdrawroot]
                action.shares = st.shares
                action.strategy = bytes_to_hex_str(st.strategy) if st.strategy else None
                action.token = bytes_to_hex_str(st.token) if st.token else None
                action.staker = bytes_to_hex_str(st.staker) if st.staker else None
                action.withdrawer = bytes_to_hex_str(st.withdrawer) if st.withdrawer else None

    def calculate_batch_result(self, eg_actions: List[EigenLayerActionD]) -> Any:
        def nested_dict():
            return defaultdict(eigen_layer_address_current_factory)

        res_d = defaultdict(nested_dict)
        for action in eg_actions:
            staker = action.staker
            strategy = action.strategy
            token = action.token
            topic0 = action.topic0
            if topic0 == self.eigen_layer_conf["DEPOSIT"]["topic"]:
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].deposit_amount += action.shares
            elif (
                topic0 == self.eigen_layer_conf["START_WITHDRAW"]["topic"]
                or topic0 == self.eigen_layer_conf["START_WITHDRAW_2"]["topic"]
            ):
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].start_withdraw_amount += action.shares
            elif topic0 == self.eigen_layer_conf["FINISH_WITHDRAW"]["topic"]:
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].finish_withdraw_amount += action.shares
            else:
                raise FastShutdownError(f"eigen_layer_job Unexpected topic {topic0}")
        return res_d


def create_nested_dict(data_list: List[EigenLayerAddressCurrentD]) -> Dict[str, Dict[str, EigenLayerAddressCurrentD]]:
    result = {}
    for item in data_list:
        if item.address and item.strategy:
            if item.address not in result:
                result[item.address] = {}
            result[item.address][item.strategy] = item
    return result
