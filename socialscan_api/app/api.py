#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx import Api

from socialscan_api.app.explorer.routes import explorer_namespace
from socialscan_api.app.l2_explorer.routes import l2_explorer_namespace

api = Api()
api.add_namespace(explorer_namespace)
api.add_namespace(l2_explorer_namespace)
