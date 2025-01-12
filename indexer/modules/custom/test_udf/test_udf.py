from typing import List
from indexer.jobs.base_job import Collector, FilterTransactionDataJob
from indexer.domain.log import Log
from indexer.utils.abi_setting import ERC20_TRANSFER_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.modules.custom.test_udf.domain.test_udf_domain import TestUdfDomain

class TestUDFJob(FilterTransactionDataJob):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        # Define the filter for ERC20 transfer events
        return TransactionFilterByLogs([
            TopicSpecification(topics=[ERC20_TRANSFER_EVENT.get_signature()])
        ])

    def _udf(self, logs: List[Log], output: Collector[TestUdfDomain]):
        """Process input data and collect output results.

        Args:
            logs: List of Log objects.
            output: Collector to collect TestUdfDomain objects.
        """
        token_transfers = []

        for log in logs:
            if log.topic0 == ERC20_TRANSFER_EVENT.get_signature():
                decoded_data = ERC20_TRANSFER_EVENT.decode_log(log)
                token_transfers.append(
                    TestUdfDomain(
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

        output.collect_domains(token_transfers)
