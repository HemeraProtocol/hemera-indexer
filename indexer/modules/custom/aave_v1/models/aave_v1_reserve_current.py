#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/11/12 10:35
# @Author  will
# @File  aave_v1_reserve_current.py
# @Brief
from sqlalchemy import BOOLEAN, INT, INTEGER, NUMERIC, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import AaveV1ReserveD, AaveV1ReserveDataCurrentD


class AaveV1ReserveCurrent(HemeraModel):
    __tablename__ = "af_aave_v1_reserve_current"
    asset = Column(BYTEA, primary_key=True)
    asset_decimals = Column(NUMERIC(100))
    asset_symbol = Column(VARCHAR)

    a_token_address = Column(BYTEA)
    a_token_decimals = Column(NUMERIC(100))
    a_token_symbol = Column(VARCHAR)

    liquidity_rate = Column(NUMERIC(100))
    stable_borrow_rate = Column(NUMERIC(100))
    variable_borrow_rate = Column(NUMERIC(100))
    liquidity_index = Column(NUMERIC(100))
    variable_borrow_index = Column(NUMERIC(100))

    interest_rate_strategy_address = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("asset"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AaveV1ReserveD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AaveV1ReserveDataCurrentD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_aave_v1_reserve_current.block_number",
                "converter": general_converter,
            },
        ]
