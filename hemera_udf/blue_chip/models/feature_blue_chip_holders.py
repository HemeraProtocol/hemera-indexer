from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, JSONB, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.blue_chip.domains import BlueChipHolder


class FeatureBlueChipHolders(HemeraModel):
    __tablename__ = "feature_blue_chip_holders"
    wallet_address = Column(BYTEA, primary_key=True)

    hold_detail = Column(JSONB)

    current_count = Column(BIGINT)

    called_block_number = Column(BIGINT)
    called_block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": BlueChipHolder,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
