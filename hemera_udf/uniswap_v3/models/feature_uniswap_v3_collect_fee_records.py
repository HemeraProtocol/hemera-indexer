from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import AgniV3TokenCollectFee, UniswapV3TokenCollectFee


class UniswapV3CollectFeeRecords(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_collect_fee_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    transaction_hash = Column(BYTEA)
    owner = Column(BYTEA)
    recipient = Column(BYTEA)

    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))
    pool_address = Column(BYTEA)
    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (
        PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number", "log_index"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3TokenCollectFee,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AgniV3TokenCollectFee,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "af_uniswap_v3_token_collect_fee_hist_pool_index",
    UniswapV3CollectFeeRecords.pool_address,
)
Index(
    "af_uniswap_v3_token_collect_fee_hist_token0_index",
    UniswapV3CollectFeeRecords.token0_address,
)
Index(
    "af_uniswap_v3_token_collect_fee_hist_token1_index",
    UniswapV3CollectFeeRecords.token1_address,
)
Index(
    "af_uniswap_v3_token_collect_fee_hist_token_id_index",
    UniswapV3CollectFeeRecords.token_id,
)
Index(
    "af_uniswap_v3_token_collect_fee_hist_owner_index",
    UniswapV3CollectFeeRecords.owner,
)
