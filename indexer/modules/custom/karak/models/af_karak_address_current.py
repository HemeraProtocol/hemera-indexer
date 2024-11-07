#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/19 15:24
# @Author  will
# @File  af_karak_address_current.py
# @Brief

from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.karak.karak_domain import KarakAddressCurrentD


class AfKarakAddressCurrent(HemeraModel):
    __tablename__ = "af_karak_address_current"
    address = Column(BYTEA, primary_key=True)

    vault = Column(BYTEA, primary_key=True)
    deposit_amount = Column(NUMERIC(100))
    start_withdraw_amount = Column(NUMERIC(100))
    finish_withdraw_amount = Column(NUMERIC(100))

    d_s = Column(NUMERIC(100))
    d_f = Column(NUMERIC(100))
    s_f = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "vault"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": KarakAddressCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
