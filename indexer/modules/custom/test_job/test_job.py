from typing import List, Union
from indexer.jobs.base_job import Collector, FilterTransactionDataJob
from indexer.domain.log import Log
from indexer.domain.token_transfer import TokenTransfer
from indexer.modules.custom.test_job.domain.test_job_domain import TestJobDomain
from indexer.utils.abi_setting import ERC20_TRANSFER_EVENT, ERC721_TRANSFER_EVENT, ERC1155_SINGLE_TRANSFER_EVENT, ERC1155_BATCH_TRANSFER_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

class TestJob(FilterTransactionDataJob):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        
        return TransactionFilterByLogs([
            TopicSpecification(topics=[ERC20_TRANSFER_EVENT.get_signature()]),
            TopicSpecification(topics=[ERC721_TRANSFER_EVENT.get_signature()]),
            TopicSpecification(topics=[ERC1155_SINGLE_TRANSFER_EVENT.get_signature()]),
            TopicSpecification(topics=[ERC1155_BATCH_TRANSFER_EVENT.get_signature()])
        ])

    def _udf(self, logs: List[Log], output: Collector[Union[TokenTransfer, TestJobDomain]]):
        token_transfers = []
        test_job_domains = []

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
                test_job_domains.append(
                    TestJobDomain(
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
            elif log.topic0 == ERC1155_SINGLE_TRANSFER_EVENT.get_signature():
                decoded_data = ERC1155_SINGLE_TRANSFER_EVENT.decode_log(log)
                test_job_domains.append(
                    TestJobDomain(
                        from_address=decoded_data["from"],
                        to_address=decoded_data["to"],
                        value=decoded_data["id"],
                        token_address=log.address,
                        block_timestamp=log.block_timestamp,
                        block_number=log.block_number,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                    )
                )
            elif log.topic0 == ERC1155_BATCH_TRANSFER_EVENT.get_signature():
                decoded_data = ERC1155_BATCH_TRANSFER_EVENT.decode_log(log)
                for i in range(len(decoded_data["ids"])):
                    test_job_domains.append(
                        TestJobDomain(
                            from_address=decoded_data["from"],
                            to_address=decoded_data["to"],
                            value=decoded_data["ids"][i],
                            token_address=log.address,
                            block_timestamp=log.block_timestamp,
                            block_number=log.block_number,
                            transaction_hash=log.transaction_hash,
                            log_index=log.log_index,
                        )
                    )

        output.collect_domains(token_transfers)
        output.collect_domains(test_job_domains)
