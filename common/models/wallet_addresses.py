from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR

from common.models import db


class WalletAddresses(db.Model):
    address = Column(VARCHAR, primary_key=True)
    ens_name = Column(VARCHAR)
