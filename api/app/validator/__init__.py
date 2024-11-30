#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 下午4:54
Author  : xuzh
Project : hemera_indexer
"""
from flask_restx.namespace import Namespace

validator_namespace = Namespace("AVS Endpoint", path="/", description="Indexed blockchain validator API")
