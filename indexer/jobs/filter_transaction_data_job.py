from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import ExtensionJob


class FilterTransactionDataJob(ExtensionJob):
    dependency_types = [Transaction]
    output_types = []
    is_filter = True

    def get_filter(self):
        raise NotImplementedError

    def get_filter_transactions(self):
        return list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
