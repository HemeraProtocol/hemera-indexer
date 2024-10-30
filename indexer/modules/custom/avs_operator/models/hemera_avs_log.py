from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class HemeraAvsOperatorLog(HemeraModel):
    __tablename__ = "hemera_avs_operator_log"
    id = Column(BIGINT, primary_key=True)
    start_block = Column(BIGINT)
    end_block = Column(BIGINT)
    data_class = Column(BYTEA)
    code_hash = Column(BYTEA)
    data_hash = Column(BYTEA)
    msg_hash = Column(BYTEA)
    count = Column(BIGINT)
    verify_status = Column(BOOLEAN)
    confirm_status = Column(BOOLEAN)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "HemeraHistoryTransparency",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
