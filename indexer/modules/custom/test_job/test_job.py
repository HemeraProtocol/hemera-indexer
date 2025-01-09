from typing import List, Union
from indexer.jobs.base_job import Collector, FilterTransactionDataJob
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer
from indexer.modules.custom.demo_job.domain.erc721_token_mint import ERC721TokenMint
from indexer.utils.abi_setting import ERC20_TRANSFER_EVENT, ERC721_TRANSFER_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
class TestJob(FilterTransactionDataJob):

    def get_filter(self):
        # Define the filter for ERC20, ERC721, and ERC1155 transfer events
        return TransactionFilterByLogs([
            TopicSpecification(topics=[ERC20_TRANSFER_EVENT.get_signature()]),
            TopicSpecification(topics=[ERC721_TRANSFER_EVENT.get_signature()])
        ])

    def _udf(self, logs: List[Log], output: Collector[Union[TokenTransfer, ERC721TokenMint]]):
        """Process input data and collect output results.

        Args:
            logs: List of Log objects.
            output: Collector to collect TokenTransfer and ERC721TokenMint objects.
        """
        token_transfers = []
        erc721_token_mints = []

        for log in logs:
            if log.topic0 == ERC20_TRANSFER_EVENT.get_signature():
                decoded_data = ERC20_TRANSFER_EVENT.decode_log(log)
                token_transfers.append(
                    TokenTransfer(
                        from_address=decoded_data["from"],
                        to_address=decoded_data["to"],
                        value=decoded_data["value"],
                        token_address=log.address,
                        block_timestamp=log.block_timestamp,
                        block_number=log.block_number,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                    )
                )
            elif log.topic0 == ERC721_TRANSFER_EVENT.get_signature():
                decoded_data = ERC721_TRANSFER_EVENT.decode_log(log)
                if decoded_data["from"] == ZERO_ADDRESS:
                    erc721_token_mints.append(
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
                else:
                    token_transfers.append(
                        TokenTransfer(
                            from_address=decoded_data["from"],
                            to_address=decoded_data["to"],
                            value=decoded_data["tokenId"],
                            token_address=log.address,
                            block_timestamp=log.block_timestamp,
                            block_number=log.block_number,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                    )

        output.collect_domains(token_transfers)
        output.collect_domains(erc721_token_mints)
