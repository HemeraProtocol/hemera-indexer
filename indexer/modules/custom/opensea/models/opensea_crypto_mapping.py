from sqlalchemy import INTEGER, VARCHAR, Column

from common.models import HemeraModel


class OpenseaCryptoTokenMapping(HemeraModel):
    __tablename__ = "af_opensea_na_crypto_token_mapping"

    address_var = Column(VARCHAR, primary_key=True)
    price_symbol = Column(VARCHAR)

    decimals = Column(INTEGER)
