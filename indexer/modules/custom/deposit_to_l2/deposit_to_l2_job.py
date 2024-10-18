import configparser
import logging
from typing import List

from eth_utils import to_normalized_address
from sqlalchemy import and_

from common.utils.abi_code_utils import Function
from common.utils.cache_utils import BlockToLiveDict, TimeToLiveDict
from common.utils.exception_control import FastShutdownError
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.deposit_to_l2.deposit_parser import parse_deposit_transaction_function, token_parse_mapping
from indexer.modules.custom.deposit_to_l2.domains.address_token_deposit import AddressTokenDeposit
from indexer.modules.custom.deposit_to_l2.domains.token_deposit_transaction import TokenDepositTransaction
from indexer.modules.custom.deposit_to_l2.models.af_token_deposits_current import AFTokenDepositsCurrent
from indexer.specification.specification import ToAddressSpecification, TransactionFilterByTransactionInfo
from indexer.utils.collection_utils import distinct_collections_by_group

logger = logging.getLogger(__name__)


class DepositToL2Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [TokenDepositTransaction, AddressTokenDeposit]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._service = kwargs["config"].get("db_service", None)
        self._contracts = set()
        self._contract_chain_mapping = {}
        self._sig_function_mapping = {}
        self._sig_parse_mapping = {}

        self._load_config()

        if self._service is None:
            raise FastShutdownError("-pg or --postgres-url is required to run DepositToL2Job")

        if self._clean_mode == "blocks":
            self.cache = BlockToLiveDict(
                retention_blocks=self._clean_limit_value, cleanup_threshold=self._clean_limit_value * 2
            )
        else:
            self.cache = TimeToLiveDict(ttl=self._clean_limit_value)

        self._filter = TransactionFilterByTransactionInfo(
            *[ToAddressSpecification(address=contract) for contract in self._contracts]
        )

    def _load_config(self):
        try:
            self._deposit_contracts = self.user_defined_config["contract_info"]
            self._clean_mode = self.user_defined_config["cache_config"].get("clean_mode", "blocks")
            self._clean_limit_value = int(self.user_defined_config["cache_config"].get("clean_limit_value", 1000))
        except Exception as e:
            message = (
                "Missing required configuration in config file. "
                "The possible reason are either that the configuration file is not specified by --config-file "
                "or the configuration for deposit_to_l2_job is missing."
            )
            logging.error(message)
            raise FastShutdownError(message)

        for chain in self._deposit_contracts.keys():
            for contract_info in self._deposit_contracts[chain]:
                contract_address = to_normalized_address(contract_info["contract"])
                self._contracts.add(contract_address)
                self._contract_chain_mapping[contract_address] = int(chain)
                for function in contract_info["ABIFunction"]:
                    abi_function = None
                    if "json" in function:
                        abi_function = Function(function["json"])
                        sig = abi_function.get_signature()
                    else:
                        sig = function["method_id"]

                    self._sig_function_mapping[sig] = abi_function
                    self._sig_parse_mapping[sig] = token_parse_mapping[function["token"]]

    def get_filter(self):
        return self._filter

    def _process(self, **kwargs):
        transactions = list(
            filter(
                self._filter.get_or_specification().is_satisfied_by,
                [
                    transaction
                    for transaction in self._data_buff[Transaction.type()]
                    if transaction.receipt and transaction.receipt.status != 0
                ],
            )
        )
        deposit_tokens = parse_deposit_transaction_function(
            transactions=transactions,
            contract_set=self._contracts,
            chain_mapping=self._contract_chain_mapping,
            sig_function_mapping=self._sig_function_mapping,
            sig_parse_mapping=self._sig_parse_mapping,
        )
        self._collect_items(TokenDepositTransaction.type(), deposit_tokens)

        if not self._reorg:
            for deposit in pre_aggregate_deposit_in_same_block(deposit_tokens):
                cache_key = (deposit.wallet_address, deposit.chain_id, deposit.contract_address, deposit.token_address)
                cache_value = self.cache.get(cache_key)
                if cache_value and cache_value.block_number < deposit.block_number:
                    # add and save 2 cache
                    token_deposit = AddressTokenDeposit(
                        wallet_address=deposit.wallet_address,
                        chain_id=deposit.chain_id,
                        contract_address=deposit.contract_address,
                        token_address=deposit.token_address,
                        value=deposit.value + cache_value.value,
                        block_number=deposit.block_number,
                        block_timestamp=deposit.block_timestamp,
                    )

                    self.cache.set(cache_key, token_deposit)
                    self._collect_item(AddressTokenDeposit.type(), token_deposit)

                elif cache_value is None:
                    # check from db and save 2 cache
                    history_deposit = self.check_history_deposit_from_db(
                        deposit.wallet_address, deposit.chain_id, deposit.token_address
                    )
                    if history_deposit is None or history_deposit.block_number < deposit.block_number:
                        token_deposit = AddressTokenDeposit(
                            wallet_address=deposit.wallet_address,
                            chain_id=deposit.chain_id,
                            contract_address=deposit.contract_address,
                            token_address=deposit.token_address,
                            value=deposit.value + history_deposit.value if history_deposit else deposit.value,
                            block_number=deposit.block_number,
                            block_timestamp=deposit.block_timestamp,
                        )
                        self.cache.set(cache_key, token_deposit)
                        self._collect_item(AddressTokenDeposit.type(), token_deposit)

            self._data_buff[AddressTokenDeposit.type()] = distinct_collections_by_group(
                collections=self._data_buff[AddressTokenDeposit.type()],
                group_by=["wallet_address", "chain_id", "contract_address", "token_address"],
                max_key="block_number",
            )

    def check_history_deposit_from_db(
        self, wallet_address: str, chain_id: int, token_address: str
    ) -> AddressTokenDeposit:
        session = self._service.get_service_session()
        try:
            history_deposit = (
                session.query(AFTokenDepositsCurrent)
                .filter(
                    and_(
                        AFTokenDepositsCurrent.wallet_address == hex_str_to_bytes(wallet_address),
                        AFTokenDepositsCurrent.chain_id == chain_id,
                        AFTokenDepositsCurrent.token_address == hex_str_to_bytes(token_address),
                    )
                )
                .first()
            )
        finally:
            session.close()

        deposit = (
            AddressTokenDeposit(
                wallet_address=bytes_to_hex_str(history_deposit.wallet_address),
                chain_id=history_deposit.chain_id,
                contract_address=bytes_to_hex_str(history_deposit.contract_address),
                token_address=bytes_to_hex_str(history_deposit.token_address),
                value=int(history_deposit.value),
                block_number=history_deposit.block_number,
                block_timestamp=int(round(history_deposit.block_timestamp.timestamp())),
            )
            if history_deposit
            else None
        )

        return deposit


def pre_aggregate_deposit_in_same_block(deposit_events: List[TokenDepositTransaction]) -> List[TokenDepositTransaction]:
    aggregated_deposit_events = {}
    for event in deposit_events:
        key = (event.wallet_address, event.chain_id, event.contract_address, event.token_address, event.block_number)
        if key in aggregated_deposit_events:
            earlier_event = aggregated_deposit_events[key]
            value = earlier_event.value + event.value
        else:
            value = event.value

        aggregated_deposit_events[key] = TokenDepositTransaction(
            transaction_hash="merged_transaction",
            wallet_address=event.wallet_address,
            chain_id=event.chain_id,
            contract_address=event.contract_address,
            token_address=event.token_address,
            value=value,
            block_number=event.block_number,
            block_timestamp=event.block_timestamp,
        )

    return [event for event in aggregated_deposit_events.values()]


if __name__ == "__main__":
    pass
