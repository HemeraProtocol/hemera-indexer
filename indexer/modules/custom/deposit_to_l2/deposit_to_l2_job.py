import configparser
import json
import os
from typing import List

from common.utils.cache_utils import BlockToLiveDict, TimeToLiveDict
from common.utils.exception_control import FastShutdownError
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.deposit_to_l2.deposit_parser import DepositToken, parse_deposit_transfer_function
from indexer.specification.specification import ToAddressSpecification, TransactionFilterByTransactionInfo


class DepositToL2Job(FilterTransactionDataJob):
    dependency_types = [Transaction]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._service = kwargs["config"].get("db_service", None)
        self._load_config("config.ini")
        self._contracts = set(
            [contract for chain in self._deposit_contracts.keys() for contract in self._deposit_contracts[chain]]
        )
        self._contract_chain_mapping = {
            contract: chain for chain in self._deposit_contracts.keys() for contract in self._deposit_contracts[chain]
        }

        if self._service is None:
            raise FastShutdownError("-pg or --postgres-url is required to run DepositToL2Job")

        if self._clean_mode == "blocks":
            self.cache = BlockToLiveDict(
                retention_blocks=self._clean_limit_value, cleanup_threshold=self._clean_limit_value * 2
            )
        else:
            self.cache = TimeToLiveDict(ttl=self._clean_limit_value)

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

    def get_filter(self):
        return TransactionFilterByTransactionInfo(
            [ToAddressSpecification(address=contract) for contract in self._contracts]
        )

    def _process(self, **kwargs):
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        deposit_tokens = parse_deposit_transfer_function(transactions, self._contracts, self._contract_chain_mapping)

        for deposit in pre_aggregate_deposit_in_same_block(deposit_tokens):
            cache_value = self.cache.get((deposit.wallet_address, deposit.chain, deposit.token_address))
            if cache_value and cache_value.block_number < deposit.block_number:
                # add and save 2 cache
                pass
            elif cache_value is None:
                # check from db and save 2 cache
                pass

        pass


def pre_aggregate_deposit_in_same_block(deposit_events: List[DepositToken]) -> List[DepositToken]:
    aggregated_deposit_events = {}
    for event in deposit_events:
        key = (event.wallet_address, event.chain, event.token_address, event.block_number)
        if key in aggregated_deposit_events:
            earlier_event = aggregated_deposit_events[key]
            event.value = earlier_event.value + event.value

        aggregated_deposit_events[key] = event

    return [event for event in aggregated_deposit_events.values()]


if __name__ == "__main__":

    pass
