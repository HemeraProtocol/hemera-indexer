import logging
from datetime import datetime

from web3._utils import blocks

from domain.block import format_block_data
from domain.block_ts_mapper import format_block_ts_mapper
from domain.log import format_log_data
from domain.transaction import format_transaction_data
from exporters.console_item_exporter import ConsoleItemExporter
from exporters.in_memory_item_exporter import InMemoryItemExporter
from enumeration.entity_type import EntityType
from jobs.export_blocks_and_transactions_job import ExportBlocksAndTransactionsJob
from jobs.export_receipts_and_logs_job import ExportReceiptsAndLogsJob
# from jobs.export_coin_balances_job import ExportCoinBalancesJob
# from jobs.export_geth_traces_job import ExportGethTracesJob
# from jobs.export_receipts_job import ExportReceiptsJob
# from jobs.export_traces_job import ExportTracesJob
# from jobs.extract_contracts_job import ExtractContractsJob
# from jobs.extract_geth_traces_job import ExtractGethTracesJob
# from jobs.extract_token_transfers_and_balances_job import ExtractTokenTransfersAndBalancesJob
# from jobs.extract_token_transfers_job import ExtractTokenTransfersJob
# from jobs.extract_tokens_job import ExtractTokensJob
from streaming.enrich import enrich_transactions, enrich_logs, enrich_token_transfers, \
    enrich_contracts, enrich_tokens, enrich_geth_traces, join, enrich_blocks_timestamp
from utils.web3_utils import build_web3


class EthStreamerAdapter:
    def __init__(
            self,
            batch_web3_provider,
            batch_web3_debug_provider,
            item_exporter=ConsoleItemExporter(),
            batch_size=100,
            max_workers=5):

        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.item_exporter = item_exporter
        self.batch_size = batch_size
        self.max_workers = max_workers

    def open(self):
        self.item_exporter.open()

    def get_current_block_number(self):
        w3 = build_web3(self.batch_web3_provider)
        return int(w3.eth.block_number)

    def export_all(self, start_block, end_block):
        # Export blocks and transactions
        blocks, transactions = self._export_blocks_and_transactions(start_block, end_block)

        # Export receipts and logs
        receipts, logs = self._export_receipts_and_logs(transactions)

        #
        # # Extract token transfers
        # token_transfers = []
        # if self._should_export(EntityType.TOKEN_TRANSFER):
        #     token_transfers = self._extract_token_transfers(logs)
        #
        # # Export traces
        # traces = []
        # if self._should_export(EntityType.TRACE):
        #     # traces = self._export_traces(start_block, end_block)
        #     block_traces = self._export_debug_traces(start_block, end_block)
        #     traces = self._extract_traces(block_traces)
        #
        # # export coin balances
        # coin_balances = []
        # if self._should_export(EntityType.COIN_BALANCE):
        #     coin_balances = self._export_coin_balances(blocks, transactions, traces)
        #
        # # Export contracts
        # contracts = []
        # if self._should_export(EntityType.CONTRACT):
        #     contracts = self._export_contracts(traces)
        #
        # # Export tokens
        # tokens = []
        # if self._should_export(EntityType.TOKEN):
        #     tokens = self._extract_tokens(contracts)

        enriched_blocks = [format_block_data(block) for block in blocks]

        enriched_transactions = [format_transaction_data(transaction)
                                 for transaction in enrich_blocks_timestamp
                                 (blocks, enrich_transactions(transactions, receipts))]

        enriched_logs = [format_log_data(log) for log in enrich_blocks_timestamp(blocks, logs)]

        # enriched_token_transfers = enrich_token_transfers(blocks, token_transfers) \
        #     if EntityType.TOKEN_TRANSFER in self.entity_types else []
        # enriched_traces = enrich_geth_traces(blocks, traces, transactions) \
        #     if EntityType.TRACE in self.entity_types else []
        # enriched_contracts = enrich_contracts(blocks, contracts) \
        #     if EntityType.CONTRACT in self.entity_types else []
        # enriched_tokens = enrich_tokens(blocks, tokens) \
        #     if EntityType.TOKEN in self.entity_types else []
        # enriched_coin_balances = coin_balances \
        #     if EntityType.COIN_BALANCE in self.entity_types else []

        block_ts_mapping = self._extract_blocks_number_timestamp_map(enriched_blocks)

        logging.info('Exporting with ' + type(self.item_exporter).__name__)

        all_items = enriched_blocks + \
                    enriched_transactions + \
                    enriched_logs + \
                    block_ts_mapping
        # enriched_token_transfers + \
        # enriched_traces + \
        # enriched_contracts + \
        # enriched_tokens + \
        # enriched_coin_balances

        self.item_exporter.export_items(all_items)

    def _export_blocks_and_transactions(self, start_block, end_block):
        job = ExportBlocksAndTransactionsJob(
            start_block=start_block,
            end_block=end_block,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            max_workers=self.max_workers,
            index_keys=['block', 'transaction']
        )
        datas = job.run()
        blocks = datas.get('block')
        transactions = datas.get('transaction')
        return blocks, transactions

    def _extract_blocks_number_timestamp_map(self, blocks):
        ts_dict = {}
        for block in blocks:
            timestamp = int(block['timestamp'] / 3600) * 3600
            block_number = block['number']

            if timestamp not in ts_dict.keys() or block_number < ts_dict[timestamp]:
                ts_dict[timestamp] = block_number
        mapping = []
        for timestamp, block_number in ts_dict.items():
            mapping.append(format_block_ts_mapper(timestamp, block_number))
        return mapping

    def _export_receipts_and_logs(self, transactions):
        job = ExportReceiptsAndLogsJob(
            transactions=transactions,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            max_workers=self.max_workers,
            index_keys=['receipt', 'log']
        )
        datas = job.run()
        receipts = datas.get('receipt')
        logs = datas.get('log')
        return receipts, logs

    #
    # def _extract_token_transfers(self, logs):
    #     exporter = InMemoryItemExporter(item_types=['token_transfer'])
    #     job = ExtractTokenTransfersJob(
    #         logs_iterable=logs,
    #         batch_size=self.batch_size,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter)
    #     job.run()
    #     token_transfers = exporter.get_items('token_transfer')
    #     return token_transfers
    #
    # def _extract_token_transfers_and_balances(self, logs):
    #     exporter = InMemoryItemExporter(item_types=['token_transfer'])
    #     job = ExtractTokenTransfersAndBalancesJob(
    #         logs_iterable=logs,
    #         batch_size=self.batch_size,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter)
    #     job.run()
    #     token_transfers = exporter.get_items('token_transfer')
    #     token_balances = exporter.get_items('token_balance')
    #     return token_transfers, token_balances
    #
    #
    # def _export_traces(self, start_block, end_block):
    #     exporter = InMemoryItemExporter(item_types=['trace'])
    #     job = ExportTracesJob(
    #         start_block=start_block,
    #         end_block=end_block,
    #         batch_size=self.batch_size,
    #         web3=ThreadLocalProxy(lambda: build_web3(self.batch_web3_provider)),
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     traces = exporter.get_items('trace')
    #     return traces
    #
    # def _export_debug_traces(self, start_block, end_block):
    #     exporter = InMemoryItemExporter(item_types=['geth_trace'])
    #     job = ExportGethTracesJob(
    #         start_block=start_block,
    #         end_block=end_block,
    #         batch_size=self.batch_size,
    #         batch_web3_provider=self.batch_web3_debug_provider,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     traces = exporter.get_items('geth_trace')
    #     return traces
    #
    # def _extract_traces(self, block_traces):
    #     exporter = InMemoryItemExporter(item_types=['trace'])
    #     job = ExtractGethTracesJob(
    #         traces_iterable=block_traces,
    #         batch_size=self.batch_size,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     traces = exporter.get_items('trace')
    #     return traces
    #
    # def _export_coin_balances(self, blocks, transactions, traces):
    #     exporter = InMemoryItemExporter(item_types=['coin_balance'])
    #     job = ExportCoinBalancesJob(
    #         blocks_iterable=blocks,
    #         transactions_iterable=transactions,
    #         traces_iterable=traces,
    #         batch_size=self.batch_size,
    #         batch_web3_provider=self.batch_web3_debug_provider,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     coin_balances = exporter.get_items('coin_balance')
    #     return coin_balances
    #
    # def _export_contracts(self, traces):
    #     exporter = InMemoryItemExporter(item_types=['contract'])
    #     job = ExtractContractsJob(
    #         traces_iterable=traces,
    #         batch_size=self.batch_size,
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     contracts = exporter.get_items('contract')
    #     return contracts
    #
    # def _extract_tokens(self, contracts):
    #     exporter = InMemoryItemExporter(item_types=['token'])
    #     job = ExtractTokensJob(
    #         contracts_iterable=contracts,
    #         web3=ThreadLocalProxy(lambda: build_web3(self.batch_web3_provider)),
    #         max_workers=self.max_workers,
    #         item_exporter=exporter
    #     )
    #     job.run()
    #     tokens = exporter.get_items('token')
    #     return tokens

    def close(self):
        self.item_exporter.close()
