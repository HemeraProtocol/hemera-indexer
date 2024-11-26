from sqlalchemy import DATE, TIMESTAMP, Column, Index, String, func, BIGINT
from sqlalchemy.dialects.postgresql import INTEGER, JSONB, NUMERIC

from common.models import HemeraModel


class PeriodWalletProtocolJsonCmeth(HemeraModel):
    __tablename__ = "period_wallet_protocol_json_cmeth"

    period_date = Column(DATE, primary_key=True)
    wallet_address = Column(String, primary_key=True)
    chain_name = Column(String, primary_key=True)
    token_symbol = Column(String, primary_key=True)
    protocol_id = Column(String, primary_key=True)
    updated_version = Column(BIGINT)

    contracts = Column(JSONB)

    total_protocol_balance = Column(NUMERIC)
    total_protocol_usd = Column(NUMERIC)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())


