from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.staking_fbtc.domains import AfStakedTransferredBalanceHistDomain


class AfStakedTransferredBalanceHist(HemeraModel):
    __tablename__ = "af_staked_transferred_balance_hist"
    contract_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_transfer_value = Column(NUMERIC(100))
    block_cumulative_value = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint("contract_address", "wallet_address", "token_address", "block_timestamp", "block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AfStakedTransferredBalanceHistDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
