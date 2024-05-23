import logging

from domain.block import format_block_data
from domain.coin_balance import format_coin_balance_data
from domain.log import format_log_data
from domain.token_balance import format_token_balance_data
from domain.token_transfer import format_token_transfer_data
from domain.trace import format_trace_data
from domain.transaction import format_transaction_data
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.export_blocks_and_transactions_job import ExportBlocksAndTransactionsJob
from jobs.export_coin_balances_job import ExportCoinBalancesJob
from jobs.export_geth_traces_job import ExportGethTracesJob
from jobs.export_receipts_and_logs_job import ExportReceiptsAndLogsJob
from jobs.export_token_balances_job import ExportTokenBalancesJob
from jobs.extract_geth_traces_job import ExtractGethTracesJob
from jobs.extract_token_transfers_job import ExtractTokenTransfersJob
from streaming import enrich
from streaming.enrich import enrich_blocks_timestamp, enrich_transactions, enrich_geth_traces
from utils.web3_utils import build_web3

logger = logging.getLogger('export_all')


def confirm_all(start_block, end_block,
                batch_web3_provider, batch_web3_debug_provider,
                item_exporter=ConsoleItemExporter(),
                export_batch_size=10,
                max_workers=5):
    item_exporter.open()

    # Export blocks and transactions
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

    # Export receipts and logs
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

    # Export traces
    job = ExportGethTracesJob(
        start_block=start_block,
        end_block=end_block,
        batch_size=export_batch_size,
        batch_web3_provider=batch_web3_debug_provider,
        max_workers=max_workers,
        index_keys=['geth_trace']
    )
    datas = job.run()
    geth_traces = datas.get('geth_trace')

    job = ExtractGethTracesJob(
        traces_iterable=geth_traces,
        batch_size=export_batch_size,
        max_workers=max_workers,
        index_keys=['trace']
    )
    datas = job.run()
    traces = datas.get('trace')

    # Export coin balances
    job = ExportCoinBalancesJob(
        blocks_iterable=blocks,
        transactions_iterable=transactions,
        traces_iterable=traces,
        batch_size=export_batch_size,
        batch_web3_provider=batch_web3_debug_provider,
        max_workers=max_workers,
        index_keys=['coin_balance']
    )
    datas = job.run()
    coin_balances = datas.get('coin_balance')

    # Extract token transfers
    job = ExtractTokenTransfersJob(
        logs_iterable=logs,
        batch_size=export_batch_size,
        max_workers=max_workers,
        index_keys=['token_transfer']
    )
    datas = job.run()
    token_transfers = datas.get('token_transfer')

    # Export token balances
    job = ExportTokenBalancesJob(
        token_transfer_iterable=token_transfers,
        batch_size=export_batch_size,
        batch_web3_provider=batch_web3_provider,
        web3=build_web3(batch_web3_provider),
        max_workers=max_workers,
        index_keys=['token_balance']
    )
    datas = job.run()
    token_balances = datas.get('token_balance')

    # enriched extra info
    enriched_blocks = [format_block_data(block) for block in blocks]

    enriched_transactions = [format_transaction_data(transaction)
                             for transaction in enrich.enrich_blocks_timestamp
                             (blocks, enrich.enrich_transactions(transactions, receipts))]

    enriched_logs = [format_log_data(log) for log in enrich.enrich_blocks_timestamp(blocks, logs)]

    enriched_traces = [format_trace_data(trace)
                       for trace in enrich.enrich_geth_traces(enriched_blocks, traces, enriched_transactions)]

    enriched_coin_balances = [format_coin_balance_data(coin_balance) for coin_balance in coin_balances]

    enriched_token_transfers = [format_token_transfer_data(token_transfer)
                                for token_transfer in enrich.enrich_blocks_timestamp(blocks, token_transfers)]

    enriched_token_balances = [format_token_balance_data(token_balance)
                               for token_balance in enrich.enrich_blocks_timestamp(blocks, token_balances)]

    # data resort
    enriched_blocks = sorted(enriched_blocks, key=lambda x: x['number'])
    enriched_transactions = sorted(enriched_transactions, key=lambda x: (x['block_number'], x['transaction_index']))
    enriched_logs = sorted(enriched_logs, key=lambda x: (x['block_number'], x['transaction_index'], x['log_index']))
    enriched_traces = sorted(enriched_traces,
                             key=lambda x: (x['block_number'], x['transaction_index'], x['trace_index']))
    enriched_coin_balances = sorted(enriched_coin_balances,
                                    key=lambda x: (x['block_number'], x['address']))
    enriched_token_transfers = sorted(enriched_token_transfers,
                                      key=lambda x: (x['block_number'], x['transaction_hash'], x['log_index']))
    enriched_token_balances = sorted(enriched_token_balances,
                                     key=lambda x: (x['block_number'], x['address']))



    # collecting data
    all_items = enriched_blocks + \
                enriched_transactions + \
                enriched_logs + \
                enriched_traces + \
                enriched_coin_balances + \
                enriched_token_transfers + \
                enriched_token_balances

    item_exporter.export_items(all_items)
    item_exporter.close()
