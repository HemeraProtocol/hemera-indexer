#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/12 10:22
# @Author  will
# @File  action_types.py
# @Brief
from enum import Enum


class OperationType(Enum):
    REGISTER = "register"
    SET_PRIMARY_NAME = "set_primary_name"
    SET_RESOLVED_ADDRESS = "set_resolved_address"
    RENEW = "renew"
    TRANSFER = "transfer"
