#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/22 11:33
# @Author  will

from sqlalchemy import BOOLEAN, INT, NUMERIC, Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.aave_v1.domains.aave_v1_domain import (
    AaveV1AddressCurrentD,
    AaveV1LiquidationAddressCurrentD,
)


class AaveV1AddressCurrent(HemeraModel):
    __tablename__ = "af_aave_v1_address_current"
    address = Column(BYTEA, primary_key=True)
    asset = Column(BYTEA, primary_key=True)

    supply_amount = Column(NUMERIC(100))
    borrow_amount = Column(NUMERIC(100))
    borrow_rate_mode = Column(INT)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    last_total_value_of_liquidation = Column(NUMERIC(100))
    last_liquidation_time = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "asset"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AaveV1AddressCurrentD,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_aave_v1_address_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": AaveV1LiquidationAddressCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
