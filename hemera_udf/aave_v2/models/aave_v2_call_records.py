#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/25 16:12
# @Author  will
# @Brief
from sqlalchemy import BOOLEAN, VARCHAR, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.aave_v2.domains.aave_v2_domain import AaveV2CallRecordsD


class AaveV2CallRecords(HemeraModel):
    __tablename__ = "af_aave_v2_call_records"
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
                "domain": AaveV2CallRecordsD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
