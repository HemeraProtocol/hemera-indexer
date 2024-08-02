#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx.namespace import Namespace

l2_explorer_namespace = Namespace(
    "Blockchain Explorer L2 Endpoint",
    path="/",
    description="Blockchain Explorer L2 API",
)
