import logging

from eth_utils import to_int, to_normalized_address

from domain.block import format_block_data
from domain.block_ts_mapper import format_block_ts_mapper
from enumeration.entity_type import EntityType
from executors.batch_work_executor import BatchWorkExecutor
from exporters.console_item_exporter import ConsoleItemExporter
from extractor.bridge.bedrock.extractor.extractor import Extractor
from jobs.base_job import BaseJob
from jobs.export_blocks_job import blocks_rpc_requests
from jobs.export_transactions_and_logs_job import receipt_rpc_requests
from utils.enrich import enrich_blocks_timestamp, enrich_transactions
from utils.utils import validate_range
from utils.web3_utils import build_web3

logger = logging.getLogger(__name__)


def format_bridge_transaction_data(transaction_dict):
    transaction = {
        'hash': transaction_dict['hash'],
        'nonce': to_int(hexstr=transaction_dict['nonce']),
        'transaction_index': to_int(hexstr=transaction_dict['transactionIndex']),
        'from_address': to_normalized_address(transaction_dict['from']),
        'to_address': to_normalized_address(transaction_dict['to']) if transaction_dict['to'] else None,
        'value': to_int(hexstr=transaction_dict['value']),
        'gas_price': to_int(hexstr=transaction_dict['gasPrice']),
        'gas': to_int(hexstr=transaction_dict['gas']),
        'transaction_type': to_int(hexstr=transaction_dict['type']) if transaction_dict['type'] else None,
        'input': transaction_dict['input'],
        'block_number': to_int(hexstr=transaction_dict['blockNumber']),
        'block_timestamp': transaction_dict['blockTimestamp'],
        'block_hash': transaction_dict['blockHash'],
        'max_fee_per_gas': to_int(hexstr=transaction_dict.get('maxFeePerGas'))
        if transaction_dict['maxFeePerGas'] else None,
        'max_priority_fee_per_gas': to_int(hexstr=transaction_dict.get('maxPriorityFeePerGas'))
        if transaction_dict['maxPriorityFeePerGas'] else None,

        'receipt': {
            'transaction_hash': transaction_dict['hash'],
            'transaction_index': to_int(hexstr=transaction_dict['transactionIndex']),
            'contract_address': to_normalized_address(transaction_dict.get('receiptContractAddress'))
            if transaction_dict.get('receiptContractAddress') else None,
            'status': to_int(hexstr=transaction_dict.get('receiptStatus'))
            if transaction_dict.get('receiptStatus') else None,
            'logs': [{
                'log_index': to_int(hexstr=log_dict['logIndex']),
                'address': to_normalized_address(log_dict['address']),
                'data': log_dict['data'],
                'topic0': log_dict['topics'][0] if len(log_dict['topics']) > 0 else None,
                'topic1': log_dict['topics'][1] if len(log_dict['topics']) > 1 else None,
                'topic2': log_dict['topics'][2] if len(log_dict['topics']) > 2 else None,
                'topic3': log_dict['topics'][3] if len(log_dict['topics']) > 3 else None,
                'transaction_hash': log_dict['transactionHash'],
                'transaction_index': to_int(hexstr=log_dict['transactionIndex']),
                'block_number': to_int(hexstr=log_dict['blockNumber']),
                'block_hash': transaction_dict['blockHash'],
                'block_timestamp': transaction_dict['blockTimestamp']
            } for log_dict in transaction_dict['logs']],
            'root': transaction_dict.get('receiptRoot', None),
            'cumulative_gas_used': to_int(hexstr=transaction_dict.get('receiptCumulativeGasUsed'))
            if transaction_dict.get('receiptCumulativeGasUsed') else None,
            'gas_used': to_int(hexstr=transaction_dict.get('receiptGasUsed'))
            if transaction_dict.get('receiptGasUsed') else None,
            'effective_gas_price': to_int(hexstr=transaction_dict.get('receiptEffectiveGasPrice'))
            if transaction_dict.get('receiptEffectiveGasPrice') else None,
            'l1_fee': to_int(hexstr=transaction_dict.get('receiptL1Fee'))
            if transaction_dict.get('receiptL1Fee') else None,
            'l1_fee_scalar': float(transaction_dict.get('receiptL1FeeScalar'))
            if transaction_dict.get('receiptL1FeeScalar') else None,
            'l1_gas_used': to_int(hexstr=transaction_dict.get('receiptL1GasUsed'))
            if transaction_dict.get('receiptL1GasUsed') else None,
            'l1_gas_price': to_int(hexstr=transaction_dict.get('receiptL1GasPrice'))
            if transaction_dict.get('receiptL1GasPrice') else None,
            'blob_gas_used': to_int(hexstr=transaction_dict.get('receiptBlobGasUsed'))
            if transaction_dict.get('receiptBlobGasUsed') else None,
            'blob_gas_price': to_int(hexstr=transaction_dict.get('receiptBlobGasPrice'))
            if transaction_dict.get('receiptBlobGasUsed') else None,
        }
    }
    return transaction




class FetchFilterDataJob(BaseJob):
    def __init__(self,
                 index_keys,
                 start_block,
                 end_block,
                 t,
                 batch_web3_provider,
                 batch_size,
                 max_workers,
                 extractor: Extractor,
                 item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys)
        validate_range(start_block, end_block)
        self.web3 = build_web3(t)
        self._start_block = start_block
        self._end_block = end_block
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._extractor = extractor
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()
        filter_params = self._extractor.get_filter()
        filter_params['fromBlock'] = self._start_block
        filter_params['toBlock'] = self._end_block

        try:
            logs = self.web3.eth.get_logs(filter_params)
        except ValueError as e:
            raise ValueError(f"Error fetching events: {e}")

        block_numbers = set([log['blockNumber'] for log in logs])
        transaction_hashes = set([log['transactionHash'] for log in logs])

        self.block_numbers = list(block_numbers)
        self.transaction_hashes = list(hash.hex() for hash in transaction_hashes)

    def _process(self):
        self._data_buff['formated_block'] = [format_block_data(block) for block in self._data_buff['block']]
        self._data_buff['formated_block'] = sorted(self._data_buff['formated_block'], key=lambda x: x['number'])

        ts_dict = {}
        for block in self._data_buff['formated_block']:
            timestamp = block['timestamp'] // 3600 * 3600
            block_number = block['number']

            if timestamp not in ts_dict.keys() or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number
        self._data_buff['block_ts_mapping'] = []
        for timestamp, block_number in ts_dict.items():
            self._data_buff['block_ts_mapping'].append(format_block_ts_mapper(timestamp, block_number))

        self._data_buff['enriched_transaction'] = [format_bridge_transaction_data(transaction)
                                                       for transaction in enrich_blocks_timestamp
                                                       (self._data_buff['formated_block'],
                                                        enrich_transactions(self._data_buff['transaction'],
                                                                            self._data_buff['receipt']))]

        self._data_buff['enriched_transaction'] = sorted(self._data_buff['enriched_transaction'],
                                                         key=lambda x: (x['block_number'],
                                                                        x['transaction_index']))

        transactions = (self._data_buff['enriched_transaction'])

        extract_data = self._extractor.extract_bridge_data(transactions)

        for data in extract_data:
            self._collect_item(data)
        print(self._data_buff)

    def _collect(self):
        self._batch_work_executor.execute(
            self.block_numbers,
            self._collect_batch,
            total_items=len(self.block_numbers)
        )
        self._batch_work_executor.shutdown()

    def _collect_batch(self, block_number_batch):
        results = blocks_rpc_requests(self._batch_web3_provider.make_request, block_number_batch, self._is_batch)
        for block in results:
            block['item'] = 'block'
            self._collect_item(block)
            for transaction in block['transactions']:
                if transaction['hash'] in self.transaction_hashes:
                    transaction['item'] = 'transaction'
                    self._collect_item(transaction)

        results = receipt_rpc_requests(self._batch_web3_provider.make_request, self.transaction_hashes, self._is_batch)
        for receipt in results:
            receipt['item'] = 'receipt'
            self._collect_item(receipt)
            for log in receipt['logs']:
                log['item'] = 'log'
                self._collect_item(log)


    def _export(self):
        export_items = self._extract_from_buff(keys= self._index_keys)
        self._item_exporter.export_items(export_items)
