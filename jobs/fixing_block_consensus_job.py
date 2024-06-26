import pandas
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from domain.block import format_block_data
from domain.coin_balance import format_coin_balance_data
from domain.contract import format_contract_data
from domain.contract_internal_transaction import trace_to_contract_internal_transaction
from domain.log import format_log_data
from domain.token import format_token_data
from domain.token_balance import format_token_balance_data
from domain.token_id_infos import format_erc721_token_id_change, format_erc721_token_id_detail, \
    format_erc1155_token_id_detail
from domain.trace import format_trace_data
from domain.transaction import format_transaction_data
from enumeration.token_type import TokenType
from exporters.jdbc.converter.postgresql_model_converter import convert_item
from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.coin_balances import CoinBalances
from exporters.jdbc.schema.contract_internal_transactions import ContractInternalTransactions
from exporters.jdbc.schema.contracts import Contracts
from exporters.jdbc.schema.erc1155_token_holders import ERC1155TokenHolders
from exporters.jdbc.schema.erc1155_token_id_details import ERC1155TokenIdDetails
from exporters.jdbc.schema.erc1155_token_transfers import ERC1155TokenTransfers
from exporters.jdbc.schema.erc20_token_holders import ERC20TokenHolders
from exporters.jdbc.schema.erc20_token_transfers import ERC20TokenTransfers
from exporters.jdbc.schema.erc721_token_holders import ERC721TokenHolders
from exporters.jdbc.schema.erc721_token_id_changes import ERC721TokenIdChanges
from exporters.jdbc.schema.erc721_token_id_details import ERC721TokenIdDetails
from exporters.jdbc.schema.erc721_token_transfers import ERC721TokenTransfers
from exporters.jdbc.schema.logs import Logs
from exporters.jdbc.schema.token_balances import AddressTokenBalances
from exporters.jdbc.schema.traces import Traces
from exporters.jdbc.schema.transactions import Transactions
from jobs.base_job import BaseJob
from jobs.export_blocks_job import blocks_rpc_requests
from jobs.export_coin_balances_job import coin_balances_rpc_requests, distinct_addresses
from jobs.export_contracts_job import build_contracts, contract_info_rpc_requests
from jobs.export_token_balances_and_holders_job import extract_token_parameters, token_balances_rpc_requests, \
    calculate_token_holders
from jobs.export_token_id_infos_job import distinct_tokens, token_ids_info_rpc_requests
from jobs.export_tokens_and_transfers_job import tokens_rpc_requests, extract_parameters_and_token_transfers, \
    get_exist_token, split_token_transfers
from jobs.export_traces_job import traces_rpc_requests
from jobs.export_transactions_and_logs_job import receipt_rpc_requests
from utils.enrich import enrich_transactions, enrich_blocks_timestamp, enrich_token_transfer_type, enrich_traces, \
    enrich_contracts
from utils.web3_utils import build_web3


class FixingBlockConsensusJob(BaseJob):
    def __init__(self,
                 service,
                 batch_web3_provider,
                 batch_web3_debug_provider):
        super().__init__()
        self.service = service
        self.batch_web3_provider = batch_web3_provider
        self.batch_web3_debug_provider = batch_web3_debug_provider
        self.web3 = build_web3(batch_web3_provider)
        self.block_number = None

    def set_fix_block_number(self, block_number):
        self.block_number = block_number

    def _collect(self):
        if self.block_number is None:
            raise ValueError(
                "Block number must be provided by using function 'set_fix_block_number', before running this job.")

        self.sign_older_block_data()

    def _process(self):
        block, origin_transactions = self.collect_fixed_block()
        self.update_fixed_block_data([block])

        transactions, logs = self.collect_fixed_transactions_logs(block, origin_transactions)
        self.update_fixed_block_data(transactions)
        self.update_fixed_block_data(logs)

        tokens, token_transfers = self.collect_fixed_tokens_and_token_transfers(logs)
        self.update_fixed_block_data(tokens)

        erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers = split_token_transfers(
            token_transfers)
        self.update_fixed_block_data(erc20_token_transfers)
        self.update_fixed_block_data(erc721_token_transfers)
        self.update_fixed_block_data(erc1155_token_transfers)

        erc721_token_ids = self.collect_fixed_token_ids_info(token_transfers, TokenType.ERC721)
        erc721_token_id_changes = [format_erc721_token_id_change(token_id_info)
                                   for token_id_info in erc721_token_ids]
        total_erc721_id_details = pandas.DataFrame([format_erc721_token_id_detail(token_id_info)
                                                    for token_id_info in erc721_token_ids])
        erc721_token_id_details = self.collect_fixed_latest_token_ids_detail(total_erc721_id_details)
        self.update_fixed_block_data(erc721_token_id_changes)
        self.update_fixed_block_data(erc721_token_id_details)

        erc1155_token_ids = self.collect_fixed_token_ids_info(token_transfers, TokenType.ERC1155)
        total_erc1155_id_details = pandas.DataFrame([format_erc1155_token_id_detail(token_id_info)
                                                     for token_id_info in erc1155_token_ids])
        erc1155_token_id_details = self.collect_fixed_latest_token_ids_detail(total_erc1155_id_details)
        self.update_fixed_block_data(erc1155_token_id_details)

        token_balances = self.collect_fixed_token_balances(token_transfers)
        self.update_fixed_block_data(token_balances)

        erc20_token_holders, erc721_token_holders, erc1155_token_holders = calculate_token_holders(token_balances)
        self.update_fixed_block_data(erc20_token_holders)
        self.update_fixed_block_data(erc721_token_holders)
        self.update_fixed_block_data(erc1155_token_holders)

        traces = self.collect_fixed_traces(block)
        internal_transaction = [trace_to_contract_internal_transaction(trace) for trace in traces]
        self.update_fixed_block_data(traces)
        self.update_fixed_block_data(internal_transaction)

        contracts = self.collect_fixed_contracts(block, traces)
        self.update_fixed_block_data(contracts)

        coin_balances = self.collect_fixed_coin_balances(block, transactions, traces)
        self.update_fixed_block_data(coin_balances)

        self.clean_unlinked_block_data()

    def sign_older_block_data(self):
        session = self.service.get_service_session()

        # sign old data
        session.query(Blocks).filter(Blocks.number == self.block_number).update({Blocks.relog: True})

        session.query(Transactions).filter(Transactions.block_number == self.block_number).update(
            {Transactions.relog: True})

        session.query(Logs).filter(Logs.block_number == self.block_number).update(
            {Logs.relog: True})

        session.query(AddressTokenBalances).filter(AddressTokenBalances.block_number == self.block_number).update(
            {AddressTokenBalances.relog: True})

        session.query(ERC20TokenTransfers).filter(ERC20TokenTransfers.block_number == self.block_number).update(
            {ERC20TokenTransfers.relog: True})

        session.query(ERC721TokenTransfers).filter(ERC721TokenTransfers.block_number == self.block_number).update(
            {ERC721TokenTransfers.relog: True})

        session.query(ERC1155TokenTransfers).filter(ERC1155TokenTransfers.block_number == self.block_number).update(
            {ERC1155TokenTransfers.relog: True})

        session.query(ERC20TokenHolders).filter(ERC20TokenHolders.block_number == self.block_number).update(
            {ERC20TokenHolders.relog: True})

        session.query(ERC721TokenHolders).filter(ERC721TokenHolders.block_number == self.block_number).update(
            {ERC721TokenHolders.relog: True})

        session.query(ERC1155TokenHolders).filter(ERC1155TokenHolders.block_number == self.block_number).update(
            {ERC1155TokenHolders.relog: True})

        session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.block_number == self.block_number).update(
            {ERC721TokenIdChanges.relog: True})

        session.query(ERC721TokenIdDetails).filter(ERC721TokenIdDetails.block_number == self.block_number).update(
            {ERC721TokenIdDetails.relog: True})

        session.query(ERC1155TokenIdDetails).filter(ERC1155TokenIdDetails.block_number == self.block_number).update(
            {ERC1155TokenIdDetails.relog: True})

        session.query(Traces).filter(Traces.block_number == self.block_number).update({Traces.relog: True})

        session.query(ContractInternalTransactions).filter(
            ContractInternalTransactions.block_number == self.block_number).update(
            {ContractInternalTransactions.relog: True})

        session.query(Contracts).filter(Contracts.block_number == self.block_number).update({Contracts.relog: True})

        session.query(CoinBalances).filter(CoinBalances.block_number == self.block_number).update(
            {CoinBalances.relog: True})

        session.commit()
        session.close()

    def clean_unlinked_block_data(self):
        session = self.service.get_service_session()

        # clean unlinked data
        session.query(Transactions).filter(Transactions.relog).delete()

        session.query(Logs).filter(Logs.relog).delete()

        session.query(AddressTokenBalances).filter(AddressTokenBalances.relog).delete()

        session.query(ERC20TokenTransfers).filter(ERC20TokenTransfers.relog).delete()

        session.query(ERC721TokenTransfers).filter(ERC721TokenTransfers.relog).delete()

        session.query(ERC1155TokenTransfers).filter(ERC1155TokenTransfers.relog).delete()

        session.query(ERC20TokenHolders).filter(ERC20TokenHolders.relog).delete()

        session.query(ERC721TokenHolders).filter(ERC721TokenHolders.relog).delete()

        session.query(ERC1155TokenHolders).filter(ERC1155TokenHolders.relog).delete()

        session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.relog).delete()

        session.query(ERC721TokenIdDetails).filter(ERC721TokenIdDetails.relog).delete()

        session.query(ERC1155TokenIdDetails).filter(ERC1155TokenIdDetails.relog).delete()

        session.query(Traces).filter(Traces.relog).delete()

        session.query(ContractInternalTransactions).filter(ContractInternalTransactions.relog).delete()

        session.query(Contracts).filter(Contracts.relog).delete()

        session.query(CoinBalances).filter(CoinBalances.relog).delete()

        session.commit()
        session.close()

    def update_fixed_block_data(self, origin_data):
        if len(origin_data) == 0:
            return

        model = origin_data[0]['model']
        db_data = [convert_item(model.__tablename__, data, fixing=True) for data in origin_data]
        session = self.service.get_service_session()

        try:
            statement = insert(model).values(db_data)

            pk_list = []
            for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
                if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
                    for column in constraint.columns:
                        pk_list.append(column.name)

            update_set = {}
            for exc in statement.excluded:
                if exc.name not in pk_list:
                    update_set[exc.name] = exc

            where_clause = None
            if 'update_strategy' in origin_data[0]:
                where_clause = text(origin_data[0]['update_strategy'])

            statement = statement.on_conflict_do_update(index_elements=pk_list, set_=update_set, where=where_clause)
            session.execute(statement)
            session.commit()
        finally:
            session.close()

    def collect_fixed_block(self):
        block_generator = blocks_rpc_requests(self.batch_web3_provider.make_batch_request, [self.block_number])
        block = [block for block in block_generator][0]
        return format_block_data(block), block['transactions']

    def collect_fixed_transactions_logs(self, block, transactions):
        receipt_generator = receipt_rpc_requests(self.batch_web3_provider.make_batch_request,
                                                 [transaction['hash'] for transaction in transactions])

        logs, receipts = [], []
        for receipt in receipt_generator:
            receipts.append(receipt)
            logs.extend(receipt['logs'])

        enriched_transactions = [format_transaction_data(transaction)
                                 for transaction in enrich_blocks_timestamp
                                 ([block], enrich_transactions(transactions, receipts))]

        enriched_logs = [format_log_data(log) for log in
                         enrich_blocks_timestamp([block], logs)]

        return enriched_transactions, enriched_logs

    def collect_fixed_tokens_and_token_transfers(self, logs):
        exist_token = get_exist_token(self.service)
        tokens_parameter, token_transfers = extract_parameters_and_token_transfers(exist_token, logs)

        tokens, tokens_type = tokens_rpc_requests(self.web3,
                                                  self.batch_web3_provider.make_batch_request,
                                                  tokens_parameter)

        format_tokens = [format_token_data(token) for token in tokens]

        return format_tokens, enrich_token_transfer_type(token_transfers, tokens_type)

    def collect_fixed_token_ids_info(self, token_transfers, token_type):
        tokens = distinct_tokens(token_transfers, token_type)
        if len(tokens) == 0:
            return []

        token_ids = token_ids_info_rpc_requests(self.web3, self.batch_web3_provider.make_batch_request, tokens)

        return token_ids

    @staticmethod
    def collect_fixed_latest_token_ids_detail(total_token_ids_detail):
        if len(total_token_ids_detail) == 0:
            return []

        token_ids_detail = total_token_ids_detail.loc[total_token_ids_detail.groupby(
            ['address', 'token_id'])['block_number'].idxmax()].to_dict(orient='records')

        return token_ids_detail

    def collect_fixed_token_balances(self, token_transfers):
        parameters = extract_token_parameters(token_transfers, self.web3)
        token_balances = token_balances_rpc_requests(self.batch_web3_provider.make_batch_request, parameters)

        return [format_token_balance_data(token_balance) for token_balance in token_balances]

    def collect_fixed_traces(self, block):
        traces = traces_rpc_requests(self.batch_web3_provider.make_batch_request, [self.block_number])
        formated_traces = [format_trace_data(trace) for trace in enrich_traces([block], traces)]

        return formated_traces

    def collect_fixed_contracts(self, block, traces):
        contracts = build_contracts(self.web3, traces)
        contracts = contract_info_rpc_requests(self.batch_web3_provider.make_batch_request, contracts)
        enriched_contract = [format_contract_data(contract) for contract in enrich_contracts([block], contracts)]

        return enriched_contract

    def collect_fixed_coin_balances(self, block, transactions, traces):
        addresses = distinct_addresses([block], transactions, traces)
        coin_balances = coin_balances_rpc_requests(self.batch_web3_provider.make_batch_request, addresses)
        formated_coin_balance = [format_coin_balance_data(coin_balance) for coin_balance in coin_balances]

        return formated_coin_balance
