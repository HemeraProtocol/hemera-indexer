#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx import Api

from api.app.address.routes import address_features_namespace
from api.app.contract.routes import contract_namespace
from api.app.explorer.routes import explorer_namespace
from api.app.l2_explorer.routes import l2_explorer_namespace
from api.app.user_operation.routes import user_operation_namespace
from custom_jobs.deposit_to_l2.endpoint.routes import token_deposit_namespace
from custom_jobs.merchant_moe.endpoints import merchant_moe_namespace
from custom_jobs.address_index.endpoint.routes import address_profile_namespace
from custom_jobs.hemera_ens.endpoint import af_ens_namespace
from custom_jobs.opensea.endpoint.routes import opensea_namespace
from custom_jobs.staking_fbtc.endpoints.routes import staking_namespace
from custom_jobs.uniswap_v3.endpoints.routes import uniswap_v3_namespace

api = Api()

api.add_namespace(explorer_namespace)
api.add_namespace(opensea_namespace)
api.add_namespace(contract_namespace)
api.add_namespace(uniswap_v3_namespace)
api.add_namespace(token_deposit_namespace)
api.add_namespace(user_operation_namespace)
api.add_namespace(staking_namespace)
api.add_namespace(merchant_moe_namespace)

api.add_namespace(l2_explorer_namespace)
api.add_namespace(af_ens_namespace)
api.add_namespace(address_profile_namespace)

api.add_namespace(address_features_namespace)
