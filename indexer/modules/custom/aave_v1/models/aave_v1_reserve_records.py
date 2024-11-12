#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/12 10:35
# @Author  will
# @File  aave_v1_reserve_records.py
# @Brief
from sqlalchemy import NUMERIC, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import AaveV1ReserveDataD


class AaveV2ReserveRates(HemeraModel):
    __tablename__ = "af_aave_v1_reserve_rates"
    asset = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)

    liquidity_rate = Column(NUMERIC(100))
    stable_borrow_rate = Column(NUMERIC(100))
    variable_borrow_rate = Column(NUMERIC(100))
    liquidity_index = Column(NUMERIC(100))
    variable_borrow_index = Column(NUMERIC(100))

    block_timestamp = Column(BIGINT)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("asset", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AaveV1ReserveDataD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
