import logging
from datetime import datetime
from typing import List, Optional, Set, Dict

from sqlalchemy import select

from common.models import db
from common.models.logs import Logs
from common.models.tokens import Tokens
from common.models.token_hourly_price import TokenHourlyPrices
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain.log import Log
from indexer.jobs.base_job import BaseJob
from indexer.modules.custom.degen_tracker.models.degen_wallet_holdings import DegenWalletHoldings
from indexer.modules.custom.degen_tracker.domain.degen_wallet import DegenWallet

logger = logging.getLogger(__name__)

class DegenTrackerJob(BaseJob):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degen_addresses = set()
        self.tracked_tokens = set()
        self._load_config()

    def _load_config(self):
        """Load degen addresses and tracked tokens from config"""
        config = self._config.get("degen_tracker_job", {})
        addresses = config.get("tracked_addresses", [])
        tokens = config.get("tracked_tokens", [])
        
        self.degen_addresses = {hex_str_to_bytes(addr.lower()) for addr in addresses}
        self.tracked_tokens = {hex_str_to_bytes(token.lower()) for token in tokens}

    def process_logs(self, logs: List[Log]) -> None:
        """Process logs to track degen wallet activities"""
        if not logs:
            return

        # Get relevant token transfers
        transfer_logs = [
            log for log in logs
            if (log.address in self.tracked_tokens or not self.tracked_tokens) and
               (log.topic0 == hex_str_to_bytes("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"))  # Transfer event
        ]

        # Extract unique addresses and tokens
        addresses = {log.topic1[12:] for log in transfer_logs}.union({log.topic2[12:] for log in transfer_logs})
        addresses = addresses.intersection(self.degen_addresses) if self.degen_addresses else addresses
        
        if not addresses:
            return

        # Update holdings for each address
        for address in addresses:
            self._update_holdings(address)

    def _update_holdings(self, address: bytes) -> None:
        """Update holdings for a specific address"""
        # Get token balances
        token_balances = self._get_token_balances(address)
        
        # Get token details and prices
        token_details = self._get_token_details(list(token_balances.keys()))
        
        # Update database
        for token_address, balance in token_balances.items():
            if token_address not in token_details:
                continue
                
            token = token_details[token_address]
            value_usd = self._get_token_value_usd(token["symbol"], balance, token["decimals"])
            
            holding = DegenWalletHoldings(
                address=address,
                token_address=token_address,
                balance=balance,
                token_symbol=token["symbol"],
                token_decimals=token["decimals"],
                last_transaction_time=datetime.now(),
                total_value_usd=value_usd,
                block_number=self._current_block_number,
                block_timestamp=datetime.now()
            )
            
            db.session.merge(holding)
        
        db.session.commit()

    def _get_token_balances(self, address: bytes) -> Dict[bytes, float]:
        """Get token balances for an address"""
        # Implementation depends on your specific needs
        # You might want to use Web3 calls or your existing database
        pass

    def _get_token_details(self, token_addresses: List[bytes]) -> Dict[bytes, Dict]:
        """Get token details from database"""
        tokens = db.session.query(Tokens).filter(
            Tokens.address.in_(token_addresses)
        ).all()
        
        return {
            token.address: {
                "symbol": token.symbol,
                "decimals": token.decimals
            }
            for token in tokens
        }

    def _get_token_value_usd(self, symbol: str, amount: float, decimals: int) -> float:
        """Get USD value of token amount"""
        price = db.session.query(TokenHourlyPrices).filter(
            TokenHourlyPrices.symbol == symbol
        ).order_by(TokenHourlyPrices.timestamp.desc()).first()
        
        if not price:
            return 0.0
            
        return float(price.price) * (amount / (10 ** decimals))
