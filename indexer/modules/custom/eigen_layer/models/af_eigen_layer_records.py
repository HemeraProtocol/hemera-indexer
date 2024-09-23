#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:29
# @Author  will
# @File  af_eigen_layer_records.py
# @Brief
from sqlalchemy import Column, Numeric, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AfEigenLayerRecords(HemeraModel):
    __tablename__ = "af_eigen_layer_records"
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    method = Column(VARCHAR)
    event_name = Column(VARCHAR)
    topic0 = Column(VARCHAR)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)

    token = Column(VARCHAR)
    vault = Column(BYTEA)
    amount = Column(NUMERIC(100))
    balance = Column(NUMERIC(100))
    staker = Column(VARCHAR)
    operator = Column(VARCHAR)
    withdrawer = Column(VARCHAR)
    shares = Column(Numeric(100))
    withdrawroot = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "N",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]