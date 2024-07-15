from indexer.cli.fixing import fixing
from indexer.cli.stream import stream
from indexer.utils.logging_utils import logging_basic_config

logging_basic_config()

import click

# from ethereumetl.cli.export_all import export_all
# from ethereumetl.cli.export_blocks_and_transactions import export_blocks_and_transactions
# from ethereumetl.cli.export_contracts import export_contracts
# from ethereumetl.cli.export_geth_traces import export_geth_traces
# from ethereumetl.cli.export_origin import export_origin
# from ethereumetl.cli.export_receipts_and_logs import export_receipts_and_logs
# from ethereumetl.cli.export_token_transfers import export_token_transfers
# from ethereumetl.cli.export_tokens import export_tokens
# from ethereumetl.cli.export_traces import export_traces
# from ethereumetl.cli.extract_contracts import extract_contracts
# from ethereumetl.cli.extract_csv_column import extract_csv_column
# from ethereumetl.cli.extract_field import extract_field
# from ethereumetl.cli.extract_geth_traces import extract_geth_traces
# from ethereumetl.cli.extract_token_transfers import extract_token_transfers
# from ethereumetl.cli.extract_tokens import extract_tokens
# from ethereumetl.cli.filter_items import filter_items
# from ethereumetl.cli.get_block_range_for_date import get_block_range_for_date
# from ethereumetl.cli.get_block_range_for_timestamps import get_block_range_for_timestamps
# from ethereumetl.cli.get_keccak_hash import get_keccak_hash


@click.group()
@click.version_option(version='2.4.2')
@click.pass_context
def cli(ctx):
    pass


# export
# cli.add_command(export_all, "export_all")
# cli.add_command(export_blocks_and_transactions, "export_blocks_and_transactions")
# cli.add_command(export_origin, "export_origin")
# cli.add_command(export_receipts_and_logs, "export_receipts_and_logs")
# cli.add_command(export_token_transfers, "export_token_transfers")
# cli.add_command(extract_token_transfers, "extract_token_transfers")
# cli.add_command(export_contracts, "export_contracts")
# cli.add_command(export_tokens, "export_tokens")
# cli.add_command(export_traces, "export_traces")
# cli.add_command(export_geth_traces, "export_geth_traces")
# cli.add_command(extract_geth_traces, "extract_geth_traces")
# cli.add_command(extract_contracts, "extract_contracts")
# cli.add_command(extract_tokens, "extract_tokens")

# streaming
cli.add_command(stream, "stream")
cli.add_command(fixing, "fixing")

# utils
# cli.add_command(get_block_range_for_date, "get_block_range_for_date")
# cli.add_command(get_block_range_for_timestamps, "get_block_range_for_timestamps")
# cli.add_command(get_keccak_hash, "get_keccak_hash")
# cli.add_command(extract_csv_column, "extract_csv_column")
# cli.add_command(filter_items, "filter_items")
# cli.add_command(extract_field, "extract_field")
