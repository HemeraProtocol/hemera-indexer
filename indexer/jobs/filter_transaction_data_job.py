from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import ExtensionJob


class FilterTransactionDataJob(ExtensionJob):
    dependency_types = [Transaction]
    output_types = []

    def get_filter(self):
        raise NotImplementedError
