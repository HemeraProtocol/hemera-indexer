import logging

from domain.block import format_block_data
from domain.log import format_log_data
from domain.transaction import format_transaction_data
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.export_blocks_and_transactions_job import ExportBlocksAndTransactionsJob
from jobs.export_receipts_and_logs_job import ExportReceiptsAndLogsJob
from streaming.enrich import enrich_blocks_timestamp, enrich_transactions

logger = logging.getLogger('export_all')


def confirm_all(start_block, end_block,
                batch_web3_provider, batch_web3_debug_provider,
                item_exporter=ConsoleItemExporter(),
                export_batch_size=10,
                max_workers=5):
    item_exporter.open()

    job = ExportBlocksAndTransactionsJob(
        start_block=start_block,
        end_block=end_block,
        batch_size=export_batch_size,
        batch_web3_provider=batch_web3_provider,
        max_workers=max_workers,
        index_keys=['block', 'transaction']
    )
    datas = job.run()
    blocks = datas.get('block')
    transactions = datas.get('transaction')

    job = ExportReceiptsAndLogsJob(
        transactions=transactions,
        batch_size=export_batch_size,
        batch_web3_provider=batch_web3_provider,
        max_workers=max_workers,
        index_keys=['receipt', 'log']
    )
    datas = job.run()
    receipts = datas.get('receipt')
    logs = datas.get('log')

    enriched_blocks = [format_block_data(block) for block in blocks]

    enriched_transactions = [format_transaction_data(transaction)
                             for transaction in enrich_blocks_timestamp
                             (blocks, enrich_transactions(transactions, receipts))]

    enriched_logs = [format_log_data(log) for log in enrich_blocks_timestamp(blocks, logs)]

    all_items = enriched_blocks + \
                enriched_transactions + \
                enriched_logs

    item_exporter.export_items(all_items)
    item_exporter.close()
