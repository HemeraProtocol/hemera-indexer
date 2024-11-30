#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/25 16:12
# @Author  will
# @File  aave_v2_address_balance_records.py
# @Brief
from sqlalchemy import BOOLEAN, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import AaveV1CallRecordsD


class AaveV1CallRecords(HemeraModel):
    __tablename__ = "af_aave_v1_call_records"
    target = Column(BYTEA, primary_key=True)
    params = Column(VARCHAR, primary_key=True)
    function = Column(VARCHAR, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    result = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("target", "params", "function", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AaveV1CallRecordsD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
