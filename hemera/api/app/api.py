#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_restx import Api

from hemera.api.app.address.routes import address_features_namespace
from hemera.api.app.contract.routes import contract_namespace
from hemera.api.app.explorer.routes import explorer_namespace
from hemera.api.app.l2_explorer.routes import l2_explorer_namespace
from hemera.api.app.user_operation.routes import user_operation_namespace
from hemera_udf.address_index.endpoint.routes import address_profile_namespace

# keep the `*`, make sure registry processed
from hemera_udf.deposit_to_l2.endpoint.routes import *
from hemera_udf.eigen_layer.endpoint.routes import *
from hemera_udf.hemera_ens.endpoint.routes import *
from hemera_udf.init_capital.endpoints.routes import *
from hemera_udf.merchant_moe.endpoints.routes import merchant_moe_namespace
from hemera_udf.opensea.endpoint.routes import *
from hemera_udf.staking_fbtc.endpoints.routes import staking_namespace
from hemera_udf.uniswap_v3.endpoints.routes import *

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
api.add_namespace(init_capital_namespace)
