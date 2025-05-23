#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 18:13
# @Author  will
# @File  af_eigen_layer_address_current.py
# @Brief
from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.eigen_layer.domains import EigenLayerAddressCurrent as EigenLayerAddressCurrentD


class AfEigenLayerAddressCurrent(HemeraModel):
    __tablename__ = "af_eigen_layer_address_current"
    address = Column(BYTEA, primary_key=True)

    strategy = Column(BYTEA, primary_key=True)
    token = Column(BYTEA)

    deposit_amount = Column(NUMERIC(100))
    start_withdraw_amount = Column(NUMERIC(100))
    finish_withdraw_amount = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "strategy"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": EigenLayerAddressCurrentD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
