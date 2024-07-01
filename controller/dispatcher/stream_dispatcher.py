from controller.dispatcher.base_dispatcher import BaseDispatcher
from enumeration.entity_type import EntityType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.check_block_consensus_job import CheckBlockConsensusJob
from jobs.export_blocks_job import ExportBlocksJob
from jobs.export_coin_balances_job import ExportCoinBalancesJob
from jobs.export_contracts_job import ExportContractsJob
from jobs.export_token_balances_and_holders_job import ExportTokenBalancesAndHoldersJob
from jobs.export_token_id_infos_job import ExportTokenIdInfosJob
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
                 debug_batch_size=1,
                 max_workers=5,
                 entity_types=255):
        super().__init__(service)
        self._batch_web3_provider = batch_web3_provider
        self._batch_web3_debug_provider = batch_web3_debug_provider
        self._web3 = build_web3(batch_web3_provider)
        self._batch_size = batch_size
        self._debug_batch_size = debug_batch_size
        self._max_workers = max_workers
        self._item_exporter = item_exporter
        self._entity_types = entity_types

    def run(self, start_block, end_block):

        if self._entity_types & EntityType.BLOCK or self._entity_types & EntityType.TRANSACTION \
                or self._entity_types & EntityType.LOG or self._entity_types & EntityType.TOKEN \
                or self._entity_types & EntityType.TOKEN_TRANSFER or self._entity_types & EntityType.COIN_BALANCE:
            ExportBlocksJob(
                index_keys=['block', 'transaction'],
                entity_types=self._entity_types,
                start_block=start_block,
                end_block=end_block,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter,
            ).run()

        if self._entity_types & EntityType.TRANSACTION or self._entity_types & EntityType.LOG \
                or self._entity_types & EntityType.TOKEN or self._entity_types & EntityType.TOKEN_TRANSFER \
                or self._entity_types & EntityType.COIN_BALANCE:
            ExportTransactionsAndLogsJob(
                index_keys=['receipt', 'log'],
                entity_types=self._entity_types,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter,
            ).run()

        if self._entity_types & EntityType.TOKEN or self._entity_types & EntityType.TOKEN_TRANSFER:
            ExportTokensAndTransfersJob(
                index_keys=['token', 'token_transfer',
                            'erc20_token_transfers', 'erc721_token_transfers', 'erc1155_token_transfers'],
                entity_types=self._entity_types,
                web3=self._web3,
                service=self._db_service,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter
            ).run()

        if self._entity_types & EntityType.TOKEN:
            ExportTokenBalancesAndHoldersJob(
                index_keys=['token_balance', 'erc20_token_holders', 'erc721_token_holders', 'erc1155_token_holders'],
                entity_types=self._entity_types,
                web3=self._web3,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter
            ).run()

            ExportTokenIdInfosJob(
                index_keys=['erc721_token_ids', 'erc1155_token_ids'],
                entity_types=self._entity_types,
                web3=self._web3,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter
            ).run()

        if self._entity_types & EntityType.TRACE or self._entity_types & EntityType.CONTRACT \
                or self._entity_types & EntityType.COIN_BALANCE:
            ExportTracesJob(
                index_keys=['trace'],
                entity_types=self._entity_types,
                start_block=start_block,
                end_block=end_block,
                batch_web3_provider=self._batch_web3_debug_provider,
                batch_size=self._debug_batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter,
            ).run()

        if self._entity_types & EntityType.TRACE or self._entity_types & EntityType.CONTRACT:
            ExportContractsJob(
                index_keys=['contract'],
                entity_types=self._entity_types,
                web3=self._web3,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter,
            ).run()

        if self._entity_types & EntityType.COIN_BALANCE:
            ExportCoinBalancesJob(
                index_keys=['coin_balance'],
                entity_types=self._entity_types,
                batch_web3_provider=self._batch_web3_provider,
                batch_size=self._batch_size,
                max_workers=self._max_workers,
                item_exporter=self._item_exporter,
            ).run()

        self._item_exporter.batch_finish()

        CheckBlockConsensusJob(entity_types=self._entity_types,
                               service=self._db_service,
                               batch_web3_provider=self._batch_web3_provider,
                               batch_web3_debug_provider=self._batch_web3_debug_provider,
                               ranges=end_block - start_block - 1,
                               batch_size=self._batch_size,
                               debug_batch_size=self._debug_batch_size,
                               ).run()
