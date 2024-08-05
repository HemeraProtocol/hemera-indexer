from indexer.domain.contract import Contract
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseJob
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordTraitsActiveness
from collections import defaultdict

from indexer.modules.custom.day_mining.domain.current_traits_activeness import CurrentTraitsActiveness
from indexer.modules.custom.day_mining.models.current_traits_activeness import CurrentTraitsActivenessModel

"""
record:
{"address": {"block_number": {'txn_count': 0, 'gas_consumed': 0}}}
latest:
{"address": {'txn_count': 0, 'gas_consumed': 0}}
"""


class ExportAllFeatureDayMiningActivenessJob(BaseJob):
    dependency_types = [Transaction]
    output_types = [AllFeatureValueRecordTraitsActiveness, CurrentTraitsActiveness]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs['config'].get('db_service'),
        self._latest_address_stats = defaultdict(
            lambda: {'txn_count': 0, 'gas_consumed': 0, 'deployed_count_count': 0})  # get from pg
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        address_stats_from_pg = self.get_latest_address_stats_from_pg()
        self._latest_address_stats.update(address_stats_from_pg)
        pass

    def get_latest_address_stats_from_pg(self):
        session = self._service[0].get_service_session()
        current_activeness_list = session.query(CurrentTraitsActivenessModel).all()
        result = {'0x' + row.address.hex(): row.value for row in current_activeness_list}
        return result

    def _process(self):
        transactions = self._data_buff[Transaction.type()]
        transactions.sort(key=lambda x: (x.block_number, x.transaction_index))

        current_batch_address_block_number_stats = defaultdict(
            lambda: defaultdict(lambda: {'txn_count': 0, 'gas_consumed': 0, 'deployed_count_count': 0}))

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
        self._data_buff[AllFeatureValueRecordTraitsActiveness.type()].sort(key=lambda x: x.block_number)

    def _calculate_latest_address_stats(self, address_block_number_stats):
        last_one_record = None

        (address, block_dict), = address_block_number_stats.items()
        for block_number, stats_value in block_dict.items():
            self._latest_address_stats[address]['txn_count'] += stats_value['txn_count']
            self._latest_address_stats[address]['gas_consumed'] += stats_value['gas_consumed']

            last_address_stats_dict = self._latest_address_stats[address]
            copy = last_address_stats_dict.copy()

            record = AllFeatureValueRecordTraitsActiveness(3, block_number, address, copy)
            self._collect_item(AllFeatureValueRecordTraitsActiveness.type(), record)
            last_one_record = CurrentTraitsActiveness(block_number, address, copy)
        if last_one_record:
            self._collect_item(CurrentTraitsActiveness.type(), last_one_record)

    @staticmethod
    def _split_address_block_number_stats(current_batch_address_block_number_stats):
        for address, block_dict in current_batch_address_block_number_stats.items():
            yield {address: block_dict}
