#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/14 11:28
# @Author  will
# @File  project_contract.py
# @Brief
from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.project_contracts.domain.project_contract_domain import ProjectContractD


class AfProjectContracts(HemeraModel):
    __tablename__ = "af_project_contracts"
    project_id = Column(VARCHAR)
    chain_id = Column(INTEGER)
    address = Column(BYTEA, primary_key=True)
    deployer = Column(BYTEA)

    transaction_from_address = Column(BYTEA)
    trace_creator = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ProjectContractD,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
