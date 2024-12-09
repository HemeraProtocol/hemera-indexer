#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from common.utils.web3_utils import ZERO_ADDRESS

# Dependency dataclass
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer
from indexer.jobs.base_job import Collector, FilterTransactionDataJob

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

    def _udf(self, logs: List[Log], output: Collector[ERC721TokenMint]):
        """Process input data and collect output results.

        Args:
            *args: Variable number of input parameters. Each parameter must be a list composed of Domain
                  subclasses. These parameters will declare existing dataclass you may need for your job.
                  The indexer will automatically run other jobs and prepare the dataclass
                  Example: List[Block], List[Transaction]

            output: A Collector type output parameter. Must declare the Domain types it will collect in its
                 generic type. The generic type will declare output dataclass your job outputs. This is helpful
                 if you write other job which depends on these dataclasses and the indexer should run this job
                 or not.
                 Example: Collector[DomainA] or Collector[Union[DomainA, DomainB]].

        Note:
            - All input parameters must be lists of Domain subclasses
            - The output parameter is required
            - The output parameter must accurately declare collected data types through generics
            - Indexer will automatically establish task dependencies and schedule based on the function signature
            - Type annotations are strictly enforced by indexer. Although Python itself does not enforce type hints,
              only _udf parameter definitions that comply with the typing rules can be executed properly.

        Example:
            >>> def _udf(self, blocks: List[Block], output: Collector[Transaction]):
            ...     # Process block data, collect transaction data
            ...     for block in blocks:
            ...         output.Collects(block.transactions)

            >>> def _udf(
            ...         self,
            ...         erc20_token_transfers: List[ERC20TokenTransfer],
            ...         erc721_token_transfers: List[ERC721TokenTransfer],
            ...         erc1155_token_transfers: List[ERC1155TokenTransfer],
            ...         output: Collector[Union[TokenBalance, CurrentTokenBalance]]
            ...     ):
            ...     # Process ERC20TokenTransfer, ERC721TokenTransfer and ERC1155TokenTransfer
            ...     # collect TokenBalance, CurrentTokenBalance
            ...     token_transfers = erc20_token_transfers + erc721_token_transfers + erc1155_token_transfers
            ...
            ...     token_balances = []
            ...     for token_transfer in token_transfers:
            ...         token_balance = deal_with(token_transfer)
            ...         output.collect(token_balance)
            ...         token_balances.append(token_balance)
            ...     current_token_balances = distinct(token_balances)
            ...     output.collects(current_token_balances)
        """

        # Core logic of UDF
        erc721_token_mints = _filter_erc721_mint_event(logs)

        # This is one of the functions that collect dataclass into unified buffer
        # The other functions can be found in indexer/jobs/base_job.py
        output.collect_domains(erc721_token_mints)
