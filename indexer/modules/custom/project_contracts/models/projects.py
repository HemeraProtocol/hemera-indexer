#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/14 11:18
# @Author  will
# @File  projects.py
# @Brief
from sqlalchemy import Column, VARCHAR, func, PrimaryKeyConstraint, TIMESTAMP, BOOLEAN, text, INT
from sqlalchemy.dialects.postgresql import JSONB, BYTEA

from common.models import HemeraModel


class AfProjects(HemeraModel):
    __tablename__ = "af_projects"
    project_id = Column(VARCHAR, primary_key=True)
    name = Column(VARCHAR)
    deployer = Column(BYTEA, primary_key=True)
    address_type = Column(INT, default=0, comment='0是作为deploy地址不参与统计；1参与统计')

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("project_id", "deployer"),)
