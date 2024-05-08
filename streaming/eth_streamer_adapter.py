import logging

from web3._utils import blocks

from domain.block import transfer_dict_to_block
from domain.log import transfer_dict_to_log
from domain.transaction import transfer_dict_to_transaction
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
# from ethereumetl.thread_local_proxy import ThreadLocalProxy
from utils.web3_utils import build_web3


class EthStreamerAdapter:
    def __init__(
            self,
            batch_web3_provider,
            batch_web3_debug_provider,
            item_exporter=ConsoleItemExporter(),
            batch_size=100,
            max_workers=5,
            entity_types=tuple(EntityType.ALL_FOR_STREAMING)):

        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.item_exporter = item_exporter
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.entity_types = entity_types

    def open(self):
        self.item_exporter.open()

    def get_current_block_number(self):
        w3 = build_web3(self.batch_web3_provider)
        return int(w3.eth.block_number)

    def export_all(self, start_block, end_block):
        # Export blocks and transactions
        blocks, transactions = [], []
        if self._should_export(EntityType.BLOCK) or self._should_export(EntityType.TRANSACTION):
            blocks, transactions = self._export_blocks_and_transactions(start_block, end_block)

        # Export receipts and logs
        receipts, logs = [], []
        if self._should_export(EntityType.RECEIPT) or self._should_export(EntityType.LOG):
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

        enriched_blocks = [transfer_dict_to_block(block) for block in blocks] \
            if EntityType.BLOCK in self.entity_types else []

        enriched_transactions = [transfer_dict_to_transaction(transaction)
                                 for transaction in enrich_blocks_timestamp
                                            (blocks, enrich_transactions(transactions, receipts))] \
            if EntityType.TRANSACTION in self.entity_types else []

        enriched_logs = [transfer_dict_to_log(log) for log in enrich_blocks_timestamp(blocks, logs)] \
            if EntityType.LOG in self.entity_types else []

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

        logging.info('Exporting with ' + type(self.item_exporter).__name__)

        all_items = enriched_blocks + \
                    enriched_transactions + \
                    enriched_logs
        # enriched_token_transfers + \
        # enriched_traces + \
        # enriched_contracts + \
        # enriched_tokens + \
        # enriched_coin_balances

        self.item_exporter.export_items(all_items)

    def _export_blocks_and_transactions(self, start_block, end_block):
        blocks_and_transactions_item_exporter = InMemoryItemExporter(item_types=['block', 'transaction'])
        blocks_and_transactions_job = ExportBlocksAndTransactionsJob(
            start_block=start_block,
            end_block=end_block,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            max_workers=self.max_workers,
            item_exporter=blocks_and_transactions_item_exporter,
            export_blocks=self._should_export(EntityType.BLOCK),
            export_transactions=self._should_export(EntityType.TRANSACTION)
        )
        blocks_and_transactions_job.run()
        blocks = blocks_and_transactions_item_exporter.get_items('block')
        transactions = blocks_and_transactions_item_exporter.get_items('transaction')
        return blocks, transactions

    def _export_receipts_and_logs(self, transactions):
        exporter = InMemoryItemExporter(item_types=['receipt', 'log'])
        job = ExportReceiptsAndLogsJob(
            transactions=transactions,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            max_workers=self.max_workers,
            item_exporter=exporter,
            export_receipts=self._should_export(EntityType.RECEIPT),
            export_logs=self._should_export(EntityType.LOG)
        )
        job.run()
        receipts = exporter.get_items('receipt')
        logs = exporter.get_items('log')
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

    def _should_export(self, entity_type):
        if entity_type == EntityType.BLOCK:
            return True

        if entity_type == EntityType.TRANSACTION:
            return EntityType.TRANSACTION in self.entity_types or self._should_export(EntityType.LOG)

        if entity_type == EntityType.RECEIPT:
            return EntityType.TRANSACTION in self.entity_types or self._should_export(EntityType.TOKEN_TRANSFER)

        if entity_type == EntityType.LOG:
            return EntityType.LOG in self.entity_types or self._should_export(EntityType.TOKEN_TRANSFER)

        if entity_type == EntityType.TOKEN_TRANSFER:
            return EntityType.TOKEN_TRANSFER in self.entity_types

        if entity_type == EntityType.TRACE:
            return EntityType.TRACE in self.entity_types or self._should_export(EntityType.CONTRACT)

        if entity_type == EntityType.CONTRACT:
            return EntityType.CONTRACT in self.entity_types or self._should_export(EntityType.TOKEN)

        if entity_type == EntityType.TOKEN:
            return EntityType.TOKEN in self.entity_types

        if entity_type == EntityType.COIN_BALANCE:
            return EntityType.COIN_BALANCE in self.entity_types or self._should_export(
                EntityType.TRANSACTION) or self._should_export(EntityType.TRACE)

        raise ValueError('Unexpected entity type ' + entity_type)

    def close(self):
        self.item_exporter.close()
