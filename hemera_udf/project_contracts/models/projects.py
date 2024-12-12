#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/14 11:18
# @Author  will
# @File  projects.py
# @Brief
from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BOOLEAN, BYTEA, INTEGER, JSONB, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel


class AfProjects(HemeraModel):
    __tablename__ = "af_projects"
    project_id = Column(VARCHAR, primary_key=True)
    name = Column(VARCHAR)
    deployer = Column(BYTEA, primary_key=True)
    address_type = Column(INTEGER, default=0, comment="0是作为deploy地址不参与统计；1参与统计")

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("project_id", "deployer"),)
