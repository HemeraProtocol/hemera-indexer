#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/20 10:11
# @Author  will
# @File  af_karak_vault_token.py
# @Brief
from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from indexer.modules.custom.karak.karak_domain import KarakVaultTokenD


class AfKarakVaultToken(HemeraModel):
    __tablename__ = "af_karak_vault_token"

    vault = Column(BYTEA, primary_key=True, nullable=False)
    token = Column(BYTEA, primary_key=True, nullable=False)
    name = Column(VARCHAR)
    symbol = Column(VARCHAR)
    asset_type = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("vault", "token"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": KarakVaultTokenD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
