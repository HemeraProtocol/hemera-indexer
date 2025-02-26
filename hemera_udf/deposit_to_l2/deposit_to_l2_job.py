import configparser
import json
import os
from typing import List, cast

from eth_typing import ABIFunction
from eth_utils import to_normalized_address

from hemera.common.utils.cache_utils import BlockToLiveDict, TimeToLiveDict
from hemera.common.utils.db_utils import build_domains_by_sql
from hemera.common.utils.exception_control import FastShutdownError
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import ToAddressSpecification, TransactionFilterByTransactionInfo
from hemera.indexer.utils.abi import function_abi_to_4byte_selector_str
from hemera.indexer.utils.collection_utils import distinct_collections_by_group
from hemera_udf.deposit_to_l2.deposit_parser import parse_deposit_transaction_function, token_parse_mapping
from hemera_udf.deposit_to_l2.domains import AddressTokenDeposit, TokenDepositTransaction


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

        self._load_config("config.ini")

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

    def _load_config(self, filename):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._deposit_contracts = json.loads(config.get("chain_deposit_info", "contract_info"))
            self._clean_mode = config.get("cache_config", "clean_mode")
            self._clean_limit_value = int(config.get("cache_config", "clean_limit_value"))
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

        for chain in self._deposit_contracts.keys():
            for contract_info in self._deposit_contracts[chain]:
                contract_address = to_normalized_address(contract_info["contract"])
                self._contracts.add(contract_address)
                self._contract_chain_mapping[contract_address] = int(chain)
                for function in contract_info["ABIFunction"]:
                    abi_function = None
                    if "json" in function:
                        abi_function = cast(ABIFunction, function["json"])
                        sig = function_abi_to_4byte_selector_str(abi_function)
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

        deposit = build_domains_by_sql(
            service=self._service,
            domain=AddressTokenDeposit,
            sql="""
            SELECT * FROM af_token_deposits_current
            WHERE
                wallet_address = '{}'
                and chain_id = {}
                and token_address = '{}'
            limit 1
            """.format(
                "\\" + wallet_address[1:], chain_id, "\\" + token_address[1:]
            ),
        )

        if len(deposit) == 0:
            deposit = None
        else:
            deposit = deposit[0]

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
