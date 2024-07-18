from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR, BYTEA

from common.models import db


class WalletAddresses(db.Model):
    address = Column(BYTEA, primary_key=True)
    ens_name = Column(VARCHAR)
