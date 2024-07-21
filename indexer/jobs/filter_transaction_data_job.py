from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import BaseJob

class FilterTransactionDataJob(BaseJob):

    dependency_types = [Transaction]

    def get_filter(self):
        raise NotImplementedError
