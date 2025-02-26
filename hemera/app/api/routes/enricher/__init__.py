#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/20 15:29
# @Author  ideal93
# @File  __init__.py.py
# @Brief
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from hemera.app.api.deps import get_read_db
from hemera.app.api.routes.enricher.address_enricher import Address, AddressEnricher, EnricherManager, EnricherType


def get_blockchain_enricher() -> AddressEnricher:
    return EnricherManager.get_instance().get_enricher()


BlockchainEnricherDep = Annotated[AddressEnricher, Depends(get_blockchain_enricher)]
