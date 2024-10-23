#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/22 14:24
# @Author  will
# @File  aave_v2_lending_records.py
# @Brief
from sqlalchemy import Column, func, BOOLEAN, text, PrimaryKeyConstraint, INTEGER, BIGINT, VARCHAR, INT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class AaveV2LendingRecords(HemeraModel):
    __tablename__ = "af_aave_v2_lending_records"

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    method = Column(VARCHAR)
    event_name = Column(VARCHAR)
    topic0 = Column(BYTEA)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)

    reserve = Column(BYTEA)
    user = Column(BYTEA)
    repayer = Column(BYTEA)
    amount = Column(BIGINT)
    on_behalf_of = Column(BYTEA)
    referral = Column(INT)
    borrow_rate_mode = Column(INT)
    borrow_rate = Column(BIGINT)
    to = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (
        PrimaryKeyConstraint(
            "transaction_hash",
            "log_index",
        ),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AaveV2DepositD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AaveV2WithdrawD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AaveV2BorrowD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AaveV2RepayD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]