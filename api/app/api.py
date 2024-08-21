#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx import Api

from api.app.custom.merchant_moe_1155_routes import custom_namespace
from api.app.custom.staked_ftbc_routes import custom_namespace
from api.app.custom.uniswap_v3_routes import custom_namespace
from api.app.explorer.routes import explorer_namespace

# from api.app.l2_explorer.routes import l2_explorer_namespace

api = Api()
api.add_namespace(explorer_namespace)
api.add_namespace(custom_namespace)
# api.add_namespace(l2_explorer_namespace)
