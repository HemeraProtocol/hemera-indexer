from indexer.domain.transaction import Transaction
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

    def get_latest_address_stats_from_pg(self):
        pass

    def _process(self):
        transactions = self._data_buff[Transaction.type()]
        transactions.sort(key=lambda x: (x.block_number, x.transaction_index))

        current_batch_address_block_number_stats = defaultdict(
            lambda: defaultdict(lambda: {'txn_count': 0, 'gas_consumed': 0}))

        # py3.6及以上dict 是有序的
        for transaction in transactions:
            if transaction.from_address != transaction.to_address:
                current_batch_address_block_number_stats[transaction.to_address][transaction.block_number][
                    'txn_count'] += 1
            current_batch_address_block_number_stats[transaction.from_address][transaction.block_number][
                'txn_count'] += 1
            current_batch_address_block_number_stats[transaction.from_address][transaction.block_number][
                'gas_consumed'] += transaction.gas * transaction.gas_price

        # 计算每个分组的 count 和 sum(tnx.gas)
        for address, block_dict in current_batch_address_block_number_stats.items():
            for block_number, stats_value in block_dict.items():
                self._latest_address_stats[address]['txn_count'] += stats_value['txn_count']
                self._latest_address_stats[address]['gas_consumed'] += stats_value['gas_consumed']

                record = AllFeatureValueRecordTraitsActiveness(3, block_number, address,
                                                               self._latest_address_stats[address])
                self._collect_item(AllFeatureValueRecordTraitsActiveness.type(), record)

    def _calculate_latest_address_stats(self, block_dict):
        for block_number, stats_value in block_dict.items():
            self._latest_address_stats[address]['txn_count'] += stats_value['txn_count']
            self._latest_address_stats[address]['gas_consumed'] += stats_value['gas_consumed']

            record = AllFeatureValueRecordTraitsActiveness(3, block_number, address,
                                                           self._latest_address_stats[address])
            self._collect_item(AllFeatureValueRecordTraitsActiveness.type(), record)
