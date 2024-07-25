import logging

import sqlalchemy
from sqlalchemy import text

from common.models.blocks import Blocks
from common.models.coin_balances import CoinBalances
from common.models.contract_internal_transactions import ContractInternalTransactions
from common.models.contracts import Contracts
from common.models.erc1155_token_id_details import ERC1155TokenIdDetails
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.erc721_token_id_changes import ERC721TokenIdChanges
from common.models.erc721_token_id_details import ERC721TokenIdDetails
from common.models.logs import Logs
from common.models.token_balances import AddressTokenBalances
from common.models.traces import Traces
from common.models.transactions import Transactions
from common.utils.web3_utils import build_web3
from enumeration.token_type import TokenType
from indexer.jobs.base_job import BaseJob
from indexer.jobs.export_blocks_job import blocks_rpc_requests
from indexer.jobs.export_traces_job import traces_rpc_requests
from indexer.jobs.export_transactions_and_logs_job import receipt_rpc_requests
from indexer.utils.utils import dynamic_batch_iterator

logger = logging.getLogger(__name__)


class FixingBlockConsensusJob(BaseJob):
   '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = kwargs['service']
        self.batch_web3_provider = kwargs['batch_web3_provider']
        self.batch_web3_debug_provider = kwargs['batch_web3_debug_provider']
        self.batch_size = kwargs['batch_size']
        self.is_batch = kwargs['batch_size'] > 1
        self.debug_batch_size = kwargs['debug_batch_size']
        self.is_debug_batch = kwargs['debug_batch_size'] > 1
        self.web3 = build_web3(kwargs['batch_web3_provider'])
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

        erc721_token_ids = self.collect_fixed_token_ids_info(token_transfers, TokenType.ERC721, ERC721TokenIdDetails)
        erc721_token_id_changes = [format_erc721_token_id_change(token_id_info)
                                   for token_id_info in erc721_token_ids]
        total_erc721_id_details = pandas.DataFrame([format_erc721_token_id_detail(token_id_info)
                                                    for token_id_info in erc721_token_ids])
        erc721_token_id_details = self.collect_fixed_latest_token_ids_detail(total_erc721_id_details)
        self.update_fixed_block_data(erc721_token_id_changes)
        self.update_fixed_block_data(erc721_token_id_details)

        erc1155_token_ids = self.collect_fixed_token_ids_info(token_transfers, TokenType.ERC1155, ERC1155TokenIdDetails)
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
        session.query(Blocks).filter(Blocks.number == self.block_number).update({Blocks.reorg: True})

        session.query(Transactions).filter(Transactions.block_number == self.block_number).update(
            {Transactions.reorg: True})

        session.query(Logs).filter(Logs.block_number == self.block_number).update(
            {Logs.reorg: True})

        session.query(AddressTokenBalances).filter(AddressTokenBalances.block_number == self.block_number).update(
            {AddressTokenBalances.reorg: True})

        session.query(ERC20TokenTransfers).filter(ERC20TokenTransfers.block_number == self.block_number).update(
            {ERC20TokenTransfers.reorg: True})

        session.query(ERC721TokenTransfers).filter(ERC721TokenTransfers.block_number == self.block_number).update(
            {ERC721TokenTransfers.reorg: True})

        session.query(ERC1155TokenTransfers).filter(ERC1155TokenTransfers.block_number == self.block_number).update(
            {ERC1155TokenTransfers.reorg: True})

        session.query(ERC20TokenHolders).filter(ERC20TokenHolders.block_number == self.block_number).update(
            {ERC20TokenHolders.reorg: True})

        session.query(ERC721TokenHolders).filter(ERC721TokenHolders.block_number == self.block_number).update(
            {ERC721TokenHolders.reorg: True})

        session.query(ERC1155TokenHolders).filter(ERC1155TokenHolders.block_number == self.block_number).update(
            {ERC1155TokenHolders.reorg: True})

        session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.block_number == self.block_number).update(
            {ERC721TokenIdChanges.reorg: True})

        session.query(ERC721TokenIdDetails).filter(ERC721TokenIdDetails.block_number == self.block_number).update(
            {ERC721TokenIdDetails.reorg: True})

        session.query(ERC1155TokenIdDetails).filter(ERC1155TokenIdDetails.block_number == self.block_number).update(
            {ERC1155TokenIdDetails.reorg: True})

        session.query(Traces).filter(Traces.block_number == self.block_number).update({Traces.reorg: True})

        session.query(ContractInternalTransactions).filter(
            ContractInternalTransactions.block_number == self.block_number).update(
            {ContractInternalTransactions.reorg: True})

        session.query(Contracts).filter(Contracts.block_number == self.block_number).update({Contracts.reorg: True})

        session.query(CoinBalances).filter(CoinBalances.block_number == self.block_number).update(
            {CoinBalances.reorg: True})

        session.commit()
        session.close()

    def clean_unlinked_block_data(self):
        session = self.service.get_service_session()

        # clean unlinked data
        session.query(Transactions).filter(Transactions.reorg).delete()

        session.query(Logs).filter(Logs.reorg).delete()

        session.query(AddressTokenBalances).filter(AddressTokenBalances.reorg).delete()

        session.query(ERC20TokenTransfers).filter(ERC20TokenTransfers.reorg).delete()

        session.query(ERC721TokenTransfers).filter(ERC721TokenTransfers.reorg).delete()

        session.query(ERC1155TokenTransfers).filter(ERC1155TokenTransfers.reorg).delete()

        session.query(ERC20TokenHolders).filter(ERC20TokenHolders.reorg).delete()

        session.query(ERC721TokenHolders).filter(ERC721TokenHolders.reorg).delete()

        session.query(ERC1155TokenHolders).filter(ERC1155TokenHolders.reorg).delete()

        session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.reorg).delete()

        session.query(ERC721TokenIdDetails).filter(ERC721TokenIdDetails.reorg).delete()

        session.query(ERC1155TokenIdDetails).filter(ERC1155TokenIdDetails.reorg).delete()

        session.query(Traces).filter(Traces.reorg).delete()

        session.query(ContractInternalTransactions).filter(ContractInternalTransactions.reorg).delete()

        session.query(Contracts).filter(Contracts.reorg).delete()

        session.query(CoinBalances).filter(CoinBalances.reorg).delete()

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

    def collect_fixed_block(self) -> Block:
        block_generator = blocks_rpc_requests(self.batch_web3_provider.make_request, [self.block_number], self.is_batch)
        block = [block for block in block_generator][0]
        return Block(block)

    def collect_fixed_transactions_logs(self, block, transactions):
        logs, receipts = [], []
        for batch in dynamic_batch_iterator([transaction['hash'] for transaction in transactions], self.batch_size):
            receipt_generator = receipt_rpc_requests(self.batch_web3_provider.make_request, batch, self.is_batch)

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
        exist_tokens = get_exist_token(self.service)
        total_tokens, token_transfers = extract_tokens_and_token_transfers(logs)

        unique_tokens = distinct_tokens(exist_tokens, total_tokens)

        tokens = []
        for batch in dynamic_batch_iterator(unique_tokens, self.batch_size):
            batch_tokens = tokens_rpc_requests(self.web3,
                                               self.batch_web3_provider.make_request,
                                               batch,
                                               self.is_batch)
            tokens.extend(batch_tokens)

        format_tokens = [format_token_data(token) for token in tokens]

        return format_tokens, token_transfers

    def collect_fixed_token_ids_info(self, token_transfers, token_type, model):
        exist_token_ids = get_exist_token_ids(self.service, model)
        tokens = distinct_token_ids(exist_token_ids, token_transfers, token_type)
        if len(tokens) == 0:
            return []

        token_ids = []
        for batch in dynamic_batch_iterator(tokens, self.batch_size):
            batch_token_ids = token_ids_info_rpc_requests(self.web3,
                                                          self.batch_web3_provider.make_request,
                                                          batch,
                                                          self.is_batch)
            token_ids.extend(batch_token_ids)

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

        token_balances = []
        for batch in dynamic_batch_iterator(parameters, self.batch_size):
            batch_token_balances = token_balances_rpc_requests(self.batch_web3_provider.make_request,
                                                               batch,
                                                               self.is_batch)
            token_balances.extend(batch_token_balances)

        return [format_token_balance_data(token_balance) for token_balance in token_balances]

    def collect_fixed_traces(self, block):
        traces = traces_rpc_requests(self.batch_web3_debug_provider.make_request,
                                     [self.block_number],
                                     self.is_debug_batch)
        formated_traces = [format_trace_data(trace) for trace in enrich_traces([block], traces)]

        return formated_traces

    def collect_fixed_contracts(self, block, traces):
        origin_contracts = build_contracts(self.web3, traces)

        contracts = []
        for batch in dynamic_batch_iterator(origin_contracts, self.batch_size):
            batch_contracts = tokens_rpc_requests(self.web3,
                                                  self.batch_web3_provider.make_request,
                                                  batch,
                                                  self.is_batch)
            contracts.extend(batch_contracts)

        enriched_contract = [format_contract_data(contract) for contract in enrich_contracts([block], contracts)]

        return enriched_contract

    def collect_fixed_coin_balances(self, block, transactions, traces):
        addresses = distinct_addresses([block], transactions, traces)

        coin_balances = []
        for batch in dynamic_batch_iterator(addresses, self.batch_size):
            batch_coin_balances = coin_balances_rpc_requests(self.batch_web3_provider.make_request,
                                                             batch,
                                                             self.is_batch)
            coin_balances.extend(batch_coin_balances)

        formated_coin_balance = [format_coin_balance_data(coin_balance) for coin_balance in coin_balances]

        return formated_coin_balance
    '''