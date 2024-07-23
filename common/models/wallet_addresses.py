from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR, BYTEA

from common.models import HemeraModel


class WalletAddresses(HemeraModel):
    address = Column(BYTEA, primary_key=True)
    ens_name = Column(VARCHAR)
