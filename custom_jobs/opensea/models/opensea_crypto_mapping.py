from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR

from common.models import HemeraModel


class OpenseaCryptoTokenMapping(HemeraModel):
    __tablename__ = "af_opensea_na_crypto_token_mapping"

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    address_var = Column(VARCHAR(42))
    price_symbol = Column(VARCHAR)
    decimals = Column(INTEGER, server_default=text("18"), nullable=False)
