from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.spectra.domains import SpectraLpBalance


class SpectraLpBalanceModel(HemeraModel):
    __tablename__ = "af_spectra_lp_balance"

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    token0_balance = Column(NUMERIC)
    token1_balance = Column(NUMERIC)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": SpectraLpBalance,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
