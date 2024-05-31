import logging

import streaming.enrich as enrich
from domain.block import format_block_data
from domain.coin_balance import format_coin_balance_data
from domain.contract import format_contract_data
from domain.contract_internal_transaction import trace_to_contract_internal_transaction
from domain.log import format_log_data
from domain.token_balance import format_token_balance_data
from domain.token_transfer import format_token_transfer_data
from domain.trace import format_trace_data, trace_is_contract_creation, trace_is_transfer_value
from domain.transaction import format_transaction_data
from domain.block_ts_mapper import format_block_ts_mapper
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.export_blocks_and_transactions_job import ExportBlocksAndTransactionsJob
from jobs.export_coin_balances_job import ExportCoinBalancesJob
from jobs.export_contracts_job import ExportContractsJob
from jobs.export_geth_traces_job import ExportGethTracesJob
from jobs.export_receipts_and_logs_job import ExportReceiptsAndLogsJob
from jobs.export_token_balances_job import ExportTokenBalancesJob
from jobs.extract_geth_traces_job import ExtractGethTracesJob
from jobs.extract_token_transfers_job import ExtractTokenTransfersJob
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
        self.web3 = build_web3(batch_web3_provider)
        self.item_exporter = item_exporter
        self.batch_size = batch_size
        self.max_workers = max_workers

    def open(self):
        self.item_exporter.open()

    def get_current_block_number(self):
        return int(self.web3.eth.block_number)

    def export_all(self, start_block, end_block):
        # Export blocks and transactions
        blocks, transactions = self._export_blocks_and_transactions(start_block, end_block)

        # Export receipts and logs
        receipts, logs = self._export_receipts_and_logs(transactions)

        # Export traces
        traces = self._export_debug_traces(start_block, end_block)

        # Extract contract and export contract name
        contracts = self._export_contracts(traces)

        # Export coin balances
        coin_balances = self._export_coin_balances(blocks, transactions, traces)

        # Extract token transfers
        token_transfers = self._extract_token_transfers(logs)

        # Export token balances
        token_balances = self._export_token_balances(token_transfers)

        # enriched data info
        enriched_blocks = [format_block_data(block) for block in blocks]

        enriched_transactions = [format_transaction_data(transaction)
                                 for transaction in enrich.enrich_blocks_timestamp
                                 (blocks, enrich.enrich_transactions(transactions, receipts))]

        enriched_logs = [format_log_data(log) for log in enrich.enrich_blocks_timestamp(blocks, logs)]

        enriched_traces = [format_trace_data(trace)
                           for trace in enrich.enrich_geth_traces(enriched_blocks, traces)]

        enriched_contract_internal_transactions = [trace_to_contract_internal_transaction(trace)
                                                   for trace in enriched_traces if
                                                   trace_is_contract_creation(trace) or
                                                   trace_is_transfer_value(trace, True)]

        enriched_coin_balances = [format_coin_balance_data(coin_balance) for coin_balance in coin_balances]

        enriched_token_transfers = [format_token_transfer_data(token_transfer)
                                    for token_transfer in enrich.enrich_blocks_timestamp(blocks, token_transfers)]

        enriched_token_balances = [format_token_balance_data(token_balance)
                                   for token_balance in enrich.enrich_blocks_timestamp(blocks, token_balances)]

        enriched_contracts = [format_contract_data(contract) for contract in
                              enrich.enrich_contracts(enriched_blocks, contracts)]

        block_ts_mapping = self._extract_blocks_number_timestamp_map(enriched_blocks)

        logging.info('Exporting with ' + type(self.item_exporter).__name__)

        all_items = enriched_transactions + \
                    enriched_logs + \
                    enriched_traces + \
                    enriched_contract_internal_transactions + \
                    enriched_contracts + \
                    enriched_coin_balances + \
                    enriched_token_transfers + \
                    enriched_token_balances + \
                    block_ts_mapping + \
                    enriched_blocks

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

    def _export_debug_traces(self, start_block, end_block):
        job = ExportGethTracesJob(
            start_block=start_block,
            end_block=end_block,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_debug_provider,
            max_workers=self.max_workers,
            index_keys=['geth_trace']
        )
        datas = job.run()
        geth_traces = datas.get('geth_trace')
        traces = self._extract_traces(geth_traces)
        return traces

    def _extract_traces(self, geth_traces):
        job = ExtractGethTracesJob(
            traces_iterable=geth_traces,
            batch_size=self.batch_size,
            max_workers=self.max_workers,
            index_keys=['trace']
        )
        datas = job.run()
        traces = datas.get('trace')
        return traces

    def _export_contracts(self, traces):
        job = ExportContractsJob(
            traces_iterable=traces,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_debug_provider,
            web3=self.web3,
            max_workers=self.max_workers,
            index_keys=['contract']
        )
        datas = job.run()
        contracts = datas.get('contract')
        return contracts

    def _export_coin_balances(self, blocks, transactions, traces):
        job = ExportCoinBalancesJob(
            blocks_iterable=blocks,
            transactions_iterable=transactions,
            traces_iterable=traces,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_debug_provider,
            max_workers=self.max_workers,
            index_keys=['coin_balance']
        )
        datas = job.run()
        coin_balances = datas.get('coin_balance')
        return coin_balances

    def _extract_token_transfers(self, logs):
        job = ExtractTokenTransfersJob(
            logs_iterable=logs,
            batch_size=self.batch_size,
            max_workers=self.max_workers,
            index_keys=['token_transfer']
        )
        datas = job.run()
        token_transfers = datas.get('token_transfer')
        return token_transfers

    def _export_token_balances(self, token_transfers):
        job = ExportTokenBalancesJob(
            token_transfer_iterable=token_transfers,
            batch_size=self.batch_size,
            batch_web3_provider=self.batch_web3_provider,
            web3=self.web3,
            max_workers=self.max_workers,
            index_keys=['token_balance']
        )
        datas = job.run()
        token_balance = datas.get('token_balance')
        return token_balance

    def close(self):
        self.item_exporter.close()
