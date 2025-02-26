#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/25 14:39
# @Author  ideal93
# @File  service.py
# @Brief
from hemera.app.core.config import settings
from hemera.app.service.extra_contract_service import ExtraContractService
from hemera.app.service.extra_ens_service import ExtraEnsService

extra_ens_service = ExtraEnsService(settings.ens_service) if settings.ens_service else None
extra_contract_service = ExtraContractService(settings.contract_service) if settings.contract_service else None
