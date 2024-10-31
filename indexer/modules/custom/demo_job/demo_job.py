#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from common.utils.web3_utils import ZERO_ADDRESS

# Dependency dataclass
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer
from indexer.jobs.base_job import FilterTransactionDataJob

# Custom dataclass
from indexer.modules.custom.demo_job.domain.erc721_token_mint import ERC721TokenMint
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

# Utility
from indexer.utils.abi_setting import ERC721_TRANSFER_EVENT


def _filter_erc721_mint_event(logs: List[Log]) -> List[TokenTransfer]:
    token_transfers = []
    for log in logs:
        if log.topic0 == ERC721_TRANSFER_EVENT.get_signature():
            decoded_data = ERC721_TRANSFER_EVENT.decode_log(log)
            if decoded_data["from"] == ZERO_ADDRESS:
                token_transfers.append(
                    ERC721TokenMint(
                        address=decoded_data["to"],
                        token_address=log.address,
                        token_id=decoded_data["tokenId"],
                        block_timestamp=log.block_timestamp,
                        block_number=log.block_number,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                    )
                )
    return token_transfers


class DemoJob(FilterTransactionDataJob):
    # Declare existing dataclass you may need for your job
    # The indexer will automatically run other jobs and prepare the dataclass
    dependency_types = [Log]

    # This is to declare output dataclass your job outputs
    # This is helpful if you write other job which depends on these dataclasses
    output_types = [ERC721TokenMint]

    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._contract_list = self.user_defined_config.get("contract_address")
        self.logger.info("Contracts to process %s", self._contract_list)

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(addresses=self._contract_list, topics=[ERC721_TRANSFER_EVENT.get_signature()])
        ]

        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        # This is how you get your dependency dataclass indexer prepared for you
        # Note that filter will apply
        logs = self._data_buff[Log.type()]

        # Core logic of UDF
        erc721_token_mints = _filter_erc721_mint_event(logs)

        # This is one of the functions that convert dataclass into models and export
        # The other functions can be found in indexer/jobs/base_job.py
        self._collect_domains(erc721_token_mints)

    def _process(self, **kwargs):
        pass
