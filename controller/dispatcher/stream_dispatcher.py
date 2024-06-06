from controller.dispatcher.base_dispatcher import BaseDispatcher
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.export_blocks_job import ExportBlocksJob
from jobs.export_coin_balances_job import ExportCoinBalancesJob
from jobs.export_contracts_job import ExportContractsJob
from jobs.export_token_balances_and_holders_job import ExportTokenBalancesAndHoldersJob
from jobs.export_tokens_and_transfers_job import ExportTokensAndTransfersJob
from jobs.export_traces_job import ExportTracesJob
from jobs.export_transactions_and_logs_job import ExportTransactionsAndLogsJob
from utils.web3_utils import build_web3


class StreamDispatcher(BaseDispatcher):

    def __init__(self,
                 service,
                 batch_web3_provider,
                 batch_web3_debug_provider,
                 item_exporter=ConsoleItemExporter(),
                 batch_size=100,
                 max_workers=5):
        super().__init__(service)
        self._batch_web3_provider = batch_web3_provider
        self._batch_web3_debug_provider = batch_web3_debug_provider
        self._web3 = build_web3(batch_web3_provider)
        self._batch_size = batch_size
        self._max_workers = max_workers
        self._item_exporter = item_exporter

    def run(self, start_block, end_block):
        ExportBlocksJob(
            index_keys=['block', 'transaction'],
            start_block=start_block,
            end_block=end_block,
            batch_web3_provider=self._batch_web3_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter,
        ).run()

        ExportTransactionsAndLogsJob(
            index_keys=['receipt', 'log'],
            batch_web3_provider=self._batch_web3_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter,
        ).run()

        ExportTokensAndTransfersJob(
            index_keys=['token', 'token_transfer',
                        'erc20_token_transfers', 'erc721_token_transfers', 'erc1155_token_transfers'],
            web3=self._web3,
            service=self._db_service,
            batch_web3_provider=self._batch_web3_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter
        ).run()

        ExportTokenBalancesAndHoldersJob(
            index_keys=['token_balance', 'erc20_token_holders', 'erc721_token_holders', 'erc1155_token_holders'],
            web3=self._web3,
            batch_web3_provider=self._batch_web3_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter
        ).run()

        ExportTracesJob(
            index_keys=['trace'],
            start_block=start_block,
            end_block=end_block,
            batch_web3_provider=self._batch_web3_debug_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter,
        ).run()

        ExportContractsJob(
            index_keys=['contract'],
            web3=self._web3,
            batch_web3_provider=self._batch_web3_debug_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter,
        ).run()

        ExportCoinBalancesJob(
            index_keys=['coin_balance'],
            batch_web3_provider=self._batch_web3_debug_provider,
            batch_size=self._batch_size,
            max_workers=self._max_workers,
            item_exporter=self._item_exporter,
        ).run()
