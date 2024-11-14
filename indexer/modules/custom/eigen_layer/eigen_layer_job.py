#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:07
# @Author  will
# @File  exportEigenLayerJob.py
# @Brief
import logging
from collections import defaultdict
from typing import Any, Dict, List

from sqlalchemy import func

from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.eigen_layer.abi import (
    DEPOSIT_EVENT,
    SHARE_WITHDRAW_QUEUED,
    WITHDRAWAL_COMPLETED_EVENT,
    WITHDRAWAL_QUEUED_BATCH_EVENT,
    WITHDRAWAL_QUEUED_EVENT,
)
from indexer.modules.custom.eigen_layer.domains.eigen_layer_domain import (
    EigenLayerAction,
    EigenLayerAddressCurrent,
    eigen_layer_address_current_factory,
)
from indexer.modules.custom.eigen_layer.models.af_eigen_layer_address_current import AfEigenLayerAddressCurrent
from indexer.modules.custom.eigen_layer.models.af_eigen_layer_records import AfEigenLayerRecords
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


"""
STRATEGY_MANAGER 0x858646372cc42e1a627fce94aa7a7033e7cf075a
deposit
share_withdrawal_queued -> withdrawal_queued
DELEGATION 0x39053d51b77dc0d36036fc1fcc8cb819df8ef37a
withdrawal_queued_batch -> withdrawal_completed
"""


class EigenLayerJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [EigenLayerAction, EigenLayerAddressCurrent]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db_service = kwargs["config"].get("db_service")
        self.chain_id = self._chain_id
        self._strategy_manager = self.user_defined_config["STRATEGY_MANAGER"]["address"]
        self._delegation = self.user_defined_config["DELEGATION"]["address"]

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                topics_filters=[
                    TopicSpecification(
                        topics=[
                            DEPOSIT_EVENT.get_signature(),
                            WITHDRAWAL_COMPLETED_EVENT.get_signature(),
                            WITHDRAWAL_QUEUED_BATCH_EVENT.get_signature(),
                            SHARE_WITHDRAW_QUEUED.get_signature(),
                            WITHDRAWAL_QUEUED_EVENT.get_signature(),
                        ],
                        addresses=[self._strategy_manager, self._delegation],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        eigen_actions = []

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if log.topic0 == DEPOSIT_EVENT.get_signature() and log.address == self._strategy_manager:
                    dl = DEPOSIT_EVENT.decode_log(log)
                    staker = dl.get("staker")
                    token = dl.get("token")
                    strategy = dl.get("strategy")
                    shares = dl.get("shares")

                    eigen_actions.append(
                        EigenLayerAction(
                            transaction_hash=transaction.hash,
                            log_index=log.log_index,
                            transaction_index=transaction.transaction_index,
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            event_name=DEPOSIT_EVENT.get_name(),
                            strategy=strategy,
                            token=token,
                            staker=staker,
                            shares=shares,
                        )
                    )
                elif log.topic0 == WITHDRAWAL_QUEUED_BATCH_EVENT.get_signature() and log.address == self._delegation:
                    dl = WITHDRAWAL_QUEUED_BATCH_EVENT.decode_log(log)

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
                        eigen_actions.append(
                            EigenLayerAction(
                                transaction_hash=transaction.hash,
                                log_index=log.log_index,
                                internal_idx=idx,
                                transaction_index=transaction.transaction_index,
                                block_number=log.block_number,
                                block_timestamp=log.block_timestamp,
                                event_name=WITHDRAWAL_QUEUED_BATCH_EVENT.get_name(),
                                strategy=strategy,
                                staker=staker,
                                withdrawer=withdrawer,
                                shares=shares,
                                withdrawroot=withdrawal_root,
                            )
                        )
                elif log.topic0 == WITHDRAWAL_QUEUED_EVENT.get_signature() and log.address == self._strategy_manager:
                    dl = WITHDRAWAL_QUEUED_EVENT.decode_log(log)

                    withdrawal_root = dl.get("withdrawalRoot")
                    staker = dl.get("depositor")
                    withdrawer = dl.get("withdrawer")
                    nonce = dl.get("nonce")
                    internal_idx = 0
                    for lg in logs:
                        if lg.topic0 == SHARE_WITHDRAW_QUEUED.get_signature():
                            dl2 = SHARE_WITHDRAW_QUEUED.decode_log(lg)
                            dl2_nonce = dl2.get("nonce")
                            if dl2_nonce == nonce:
                                shares = dl2.get("shares")
                                strategy = dl2.get("strategy")

                                action = EigenLayerAction(
                                    transaction_hash=transaction.hash,
                                    log_index=log.log_index,
                                    internal_idx=internal_idx,
                                    transaction_index=transaction.transaction_index,
                                    block_number=log.block_number,
                                    block_timestamp=log.block_timestamp,
                                    event_name=WITHDRAWAL_QUEUED_EVENT.get_name(),
                                    strategy=strategy,
                                    staker=staker,
                                    shares=shares,
                                    withdrawer=withdrawer,
                                    withdrawroot=withdrawal_root,
                                )
                                internal_idx += 1
                                eigen_actions.append(action)
                elif log.topic0 == WITHDRAWAL_COMPLETED_EVENT.get_signature() and log.address == self._delegation:
                    dl = WITHDRAWAL_COMPLETED_EVENT.decode_log(log)
                    withdrawal_root = dl.get("withdrawalRoot")
                    eigen_actions.append(
                        EigenLayerAction(
                            transaction_hash=transaction.hash,
                            log_index=log.log_index,
                            transaction_index=transaction.transaction_index,
                            internal_idx=0,
                            block_number=log.block_number,
                            block_timestamp=log.block_timestamp,
                            event_name=WITHDRAWAL_COMPLETED_EVENT.get_name(),
                            strategy=None,
                            token=None,
                            staker=None,
                            shares=None,
                            withdrawer=None,
                            withdrawroot=withdrawal_root,
                        )
                    )
        self.enrich_complete_withdraw(eigen_actions)
        self._collect_domains(eigen_actions)

        batch_result_dic = self.calculate_batch_result(eigen_actions)
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

    def get_existing_address_current(self, addresses):
        if not self.db_service:
            return {}

        addresses = [hex_str_to_bytes(address) for address in addresses if address]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            query = session.query(AfEigenLayerAddressCurrent).filter(AfEigenLayerAddressCurrent.address.in_(addresses))
            result = query.all()
        lis = []
        for rr in result:
            lis.append(
                EigenLayerAddressCurrent(
                    address=bytes_to_hex_str(rr.address),
                    strategy=bytes_to_hex_str(rr.strategy),
                    token=bytes_to_hex_str(rr.token) if rr.token else None,
                    deposit_amount=rr.deposit_amount,
                    start_withdraw_amount=rr.start_withdraw_amount,
                    finish_withdraw_amount=rr.finish_withdraw_amount,
                )
            )

        return create_nested_dict(lis)

    def enrich_complete_withdraw(self, actions: List[EigenLayerAction]):
        roots = [
            action.withdrawroot for action in actions if action.event_name == WITHDRAWAL_COMPLETED_EVENT.get_name()
        ]
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
            if action.event_name == WITHDRAWAL_COMPLETED_EVENT.get_name():
                st = ac_map[action.withdrawroot]
                action.shares = st.shares
                action.strategy = bytes_to_hex_str(st.strategy) if st.strategy else None
                action.token = bytes_to_hex_str(st.token) if st.token else None
                action.staker = bytes_to_hex_str(st.staker) if st.staker else None
                action.withdrawer = bytes_to_hex_str(st.withdrawer) if st.withdrawer else None

    def calculate_batch_result(self, eigen_actions: List[EigenLayerAction]) -> Any:
        def nested_dict():
            return defaultdict(eigen_layer_address_current_factory)

        res_d = defaultdict(nested_dict)
        for action in eigen_actions:
            staker = action.staker
            strategy = action.strategy
            token = action.token
            event_name = action.event_name
            if event_name == DEPOSIT_EVENT.get_name():
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].deposit_amount += action.shares
            elif (
                event_name == WITHDRAWAL_QUEUED_EVENT.get_name()
                or event_name == WITHDRAWAL_QUEUED_BATCH_EVENT.get_name()
            ):
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].start_withdraw_amount += action.shares
            elif event_name == WITHDRAWAL_COMPLETED_EVENT.get_name():
                res_d[staker][strategy].address = staker
                res_d[staker][strategy].token = token
                res_d[staker][strategy].strategy = strategy
                res_d[staker][strategy].finish_withdraw_amount += action.shares
            else:
                raise FastShutdownError(f"eigen_layer_job Unexpected event {event_name}")
        return res_d


def create_nested_dict(data_list: List[EigenLayerAddressCurrent]) -> Dict[str, Dict[str, EigenLayerAddressCurrent]]:
    result = {}
    for item in data_list:
        if item.address and item.strategy:
            if item.address not in result:
                result[item.address] = {}
            result[item.address][item.strategy] = item
    return result
