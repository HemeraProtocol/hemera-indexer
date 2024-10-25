#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/25 16:12
# @Author  will
# @File  aave_v2_address_balance_records.py
# @Brief
from sqlalchemy import BOOLEAN, NUMERIC, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class AaveV2AddressBalanceRecords(HemeraModel):
    __tablename__ = "af_aave_v2_address_balance_records"
    address = Column(BYTEA, primary_key=True)
    token = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AaveV2AddressBalanceRecordsD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
