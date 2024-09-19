#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/19 15:24
# @Author  will
# @File  af_karak_address_current.py
# @Brief
from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AfKarakAddressCurrent(HemeraModel):
    __tablename__ = "af_karak_address_current"
    address = Column(BYTEA, primary_key=True)

    vault = Column(BYTEA)
    amount = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3SwapEvent",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AgniV3SwapEvent",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
