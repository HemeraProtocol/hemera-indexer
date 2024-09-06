#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx import Api

from api.app.contract.routes import contract_namespace
from api.app.explorer.routes import explorer_namespace
from api.app.user_operation.routes import user_operation_namespace
from indexer.modules.custom.uniswap_v3.endpoints.routes import uniswap_v3_namespace
from indexer.modules.custom.opensea.endpoint.routes import opensea_namespace

# from api.app.l2_explorer.routes import l2_explorer_namespace

api = Api()

api.add_namespace(explorer_namespace)
api.add_namespace(user_operation_namespace)
api.add_namespace(opensea_namespace)
api.add_namespace(contract_namespace)
api.add_namespace(uniswap_v3_namespace)
# api.add_namespace(l2_explorer_namespace)
