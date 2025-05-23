#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/10/14 11:42
# @Author  will
# @File  project_contract_domain.py
# @Brief
from dataclasses import dataclass
from typing import Optional

from hemera.indexer.domains import Domain


@dataclass
class ProjectContractD(Domain):

    project_id: Optional[str] = None
    chain_id: Optional[int] = None
    address: Optional[str] = None
    deployer: Optional[str] = None

    transaction_from_address: Optional[str] = None
    trace_creator: Optional[str] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
