from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP
from uniswap_v2 import UniswapV2Erc20CurrentTotalSupply

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.total_supply.domains import Erc20CurrentTotalSupply


class AfErc20TotalSupplyCurrent(HemeraModel):
    __tablename__ = "af_erc20_total_supply_current"
    token_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Erc20CurrentTotalSupply,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_erc20_total_supply_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": UniswapV2Erc20CurrentTotalSupply,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_erc20_total_supply_current.block_number",
                "converter": general_converter,
            },
        ]
