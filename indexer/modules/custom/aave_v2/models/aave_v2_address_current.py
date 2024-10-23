#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/22 11:33
# @Author  will

from sqlalchemy import Column, func, BOOLEAN, text, PrimaryKeyConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class AaveV2AddressCurrent(HemeraModel):
    __tablename__ = "af_aave_v2_address_current"
    address = Column(BYTEA, primary_key=True)
    asset = Column(BYTEA, primary_key=True)

    supply_amount = Column(BIGINT)
    borrow_amount = Column(BIGINT)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    total_value_of_liquidation = Column(BIGINT)
    liquidation_time = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "asset"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AaveV2AddressCurrentD",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_aave_v2_address_current.block_number",
                "converter": general_converter,
            },
        ]
