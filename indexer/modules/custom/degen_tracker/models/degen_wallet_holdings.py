from sqlalchemy import Column, Index, TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, FLOAT, INTEGER, VARCHAR

from common.models import HemeraModel

class DegenWalletHoldings(HemeraModel):
    __tablename__ = "degen_wallet_holdings"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(FLOAT)
    token_symbol = Column(VARCHAR)
    token_decimals = Column(INTEGER)
    last_transaction_time = Column(TIMESTAMP)
    total_value_usd = Column(FLOAT)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

# Create indexes for efficient querying
Index('degen_wallet_holdings_address_idx', DegenWalletHoldings.address)
Index('degen_wallet_holdings_token_address_idx', DegenWalletHoldings.token_address)
Index('degen_wallet_holdings_value_idx', DegenWalletHoldings.total_value_usd.desc())
