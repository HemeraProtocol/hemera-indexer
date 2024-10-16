import logging
from collections import defaultdict
from typing import List

from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob
from indexer.modules.custom.project_contracts.domain.project_contract_domain import ProjectContractD
from indexer.modules.custom.project_contracts.models.project_contract import AfProjectContracts
from indexer.modules.custom.project_contracts.models.projects import AfProjects

from indexer.utils.abi import bytes_to_hex_str

logger = logging.getLogger(__name__)


class ExportProjectContractsJob(ExtensionJob):
    dependency_types = [Transaction, Trace]
    output_types = [ProjectContractD]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self.db_service = kwargs["config"].get("db_service")
        self.chain_id = self._web3.eth.chain_id
        self.trace_type_prefix = 'create'

        self.project_deployers = defaultdict(list)
        self.project_contracts = defaultdict(set)
        self.project_map = dict()
        self.current_project_id = None
        self.current_deployer = None
        self.transaction_map = dict()
        self.trace_map = dict()
        self.contract_map = dict()
        self.read_configured_projects()

    def _collect(self, **kwargs):
        transactions = self._data_buff[Transaction.type()]
        transaction_map = {tnx.hash: tnx for tnx in transactions}
        self.transaction_map = transaction_map
        traces = self._data_buff[Trace.type()]
        filtered_trace_list = [trace for trace in traces if
                               trace.trace_type.startswith(self.trace_type_prefix) and trace.status == 1]

        res = []
        for project_id, deployers in self.project_deployers.items():
            project = self.project_map[project_id]
            self.current_project_id = project_id
            if project_id == 'uniswapv3':
                print('ok')
            for deployer in deployers:
                res.extend(self.direct_create_contracts(deployer, filtered_trace_list, transactions))
                res.extend(self.contract_create_contracts(filtered_trace_list, transactions))
        self._collect_items(ProjectContractD.type(), res)

    def read_configured_projects(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjects)
            result = query.all()
        for project in result:
            self.project_deployers[project.project_id].append(bytes_to_hex_str(project.deployer))
            self.project_map[project.project_id] = project

    def read_discovered_contracts(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjectContracts)
            result = query.all()
        for project_contract in result:
            self.project_contracts[project_contract.project_id].add(bytes_to_hex_str(project_contract.contract))

    def fetch_result(self, query):
        with self.db_service.get_service_session() as session:
            result = session.execute(query)
        return result

    def direct_create_contracts(self, deployer, filtered_trace_list: List[Trace], transactions: List[Transaction]):

        filtered_transactions_hash_set = set([tn.hash for tn in transactions if tn.from_address == deployer])
        res = []
        for ta in filtered_trace_list:
            if ta.transaction_hash in filtered_transactions_hash_set:
                create_transaction = self.transaction_map[ta.transaction_hash]
                res.append(ProjectContractD(
                    address=create_transaction.to_address,
                    project_id=self.current_project_id,
                    chain_id=self.chain_id,
                    deployer=self.current_deployer,
                    transaction_from_address=create_transaction.from_address,
                    trace_creator=None,
                    block_number=create_transaction.block_number,
                    block_timestamp=create_transaction.block_timestamp,
                    transaction_hash=create_transaction.hash
                ))
        return res

    def contract_create_contracts(self, filtered_trace_list: List[Trace],
                                  transactions: List[Transaction]):
        res = []
        for tr in filtered_trace_list:
            if tr.from_address in self.project_contracts[self.current_project_id]:
                create_transaction = self.transaction_map[tr.transaction_hash]
                res.append(ProjectContractD(
                    address=tr.to_address,
                    project_id=self.current_project_id,
                    chain_id=self.chain_id,
                    deployer=self.current_deployer,
                    transaction_from_address=create_transaction.from_address,
                    trace_creator=None,
                    block_number=create_transaction.block_number,
                    block_timestamp=create_transaction.block_timestamp,
                    transaction_hash=create_transaction.hash
                ))
        return res
