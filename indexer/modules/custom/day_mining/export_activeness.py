from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordTraitsActiveness
from collections import defaultdict, OrderedDict

"""
record:
{"address": {"block_number": {'txn_count': 0, 'gas_consumed': 0}}}
latest:
{"address": {'txn_count': 0, 'gas_consumed': 0}}
"""


class ExportAllFeatureDayMiningActivenessJob(BaseJob):
    dependency_types = [Transaction]
    output_types = [AllFeatureValueRecordTraitsActiveness]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs['config'].get('db_service'),
        self._latest_address_stats = defaultdict(lambda: {'txn_count': 0, 'gas_consumed': 0})  # get from pg
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

    def get_latest_address_stats_from_pg(self):
        pass

    def _process(self):
        transactions = self._data_buff[Transaction.type()]
        transactions.sort(key=lambda x: (x.block_number, x.transaction_index))

        current_batch_address_block_number_stats = defaultdict(
            lambda: defaultdict(lambda: {'txn_count': 0, 'gas_consumed': 0}))

        # py3.6 and above dict is ordered
        for transaction in transactions:
            if transaction.from_address != transaction.to_address:
                current_batch_address_block_number_stats[transaction.to_address][transaction.block_number][
                    'txn_count'] += 1
            current_batch_address_block_number_stats[transaction.from_address][transaction.block_number][
                'txn_count'] += 1
            current_batch_address_block_number_stats[transaction.from_address][transaction.block_number][
                'gas_consumed'] += transaction.gas * transaction.gas_price

        self._batch_work_executor.execute(current_batch_address_block_number_stats,
                                          self._calculate_latest_address_stats,
                                          total_items=len(current_batch_address_block_number_stats),
                                          split_method=self._split_address_block_number_stats)
        self._batch_work_executor.wait()

    def _calculate_latest_address_stats(self, address_block_number_stats):
        (address, block_dict), = address_block_number_stats.items()
        for block_number, stats_value in block_dict.items():
            self._latest_address_stats[address]['txn_count'] += stats_value['txn_count']
            self._latest_address_stats[address]['gas_consumed'] += stats_value['gas_consumed']

            last_address_stats_dict = self._latest_address_stats[address]
            copy = last_address_stats_dict.copy()

            record = AllFeatureValueRecordTraitsActiveness(3, block_number, address,
                                                           copy)
            self._collect_item(AllFeatureValueRecordTraitsActiveness.type(), record)

    @staticmethod
    def _split_address_block_number_stats(current_batch_address_block_number_stats):
        for address, block_dict in current_batch_address_block_number_stats.items():
            yield {address: block_dict}
