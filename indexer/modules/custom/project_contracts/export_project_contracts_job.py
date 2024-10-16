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
        self.trace_type_prefix = "create"

        self.project_deployers = defaultdict(list)
        self.project_contracts = defaultdict(set)
        self.transaction_map = dict()

        self.read_configured_projects()
        self.read_discovered_contracts()

    def _collect(self, **kwargs):
        transactions = self._data_buff[Transaction.type()]
        transactions = [
            a_transaction
            for a_transaction in transactions
            if a_transaction.receipt and a_transaction.receipt.status == 1
        ]
        traces = self._data_buff[Trace.type()]

        self.transaction_map = {tnx.hash: tnx for tnx in transactions}
        filtered_trace_list = [
            trace for trace in traces if trace.trace_type.startswith(self.trace_type_prefix) and trace.status == 1
        ]

        res = []
        for project_id, deployers in self.project_deployers.items():
            for deployer in deployers:
                res.extend(self.direct_create_contracts(project_id, deployer, filtered_trace_list, transactions))
                res.extend(self.contract_create_contracts(project_id, deployer, filtered_trace_list))
        self._collect_items(ProjectContractD.type(), res)
        # merge new contracts into exists
        for pc in res:
            self.project_contracts[pc.project_id].add(pc.address)
        self.transaction_map.clear()

    def read_configured_projects(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjects)
            result = query.all()
        for project in result:
            self.project_deployers[project.project_id].append(bytes_to_hex_str(project.deployer))

    def read_discovered_contracts(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjectContracts)
            result = query.all()
        for project_contract in result:
            self.project_contracts[project_contract.project_id].add(bytes_to_hex_str(project_contract.address))

    def direct_create_contracts(
        self, project_id, deployer, filtered_trace_list: List[Trace], transactions: List[Transaction]
    ):

        filtered_transactions_hash_set = set([tn.hash for tn in transactions if tn.from_address == deployer])
        res = []
        for a_trace in filtered_trace_list:
            if a_trace.transaction_hash in filtered_transactions_hash_set:
                create_transaction = self.transaction_map[a_trace.transaction_hash]
                res.append(
                    ProjectContractD(
                        address=create_transaction.to_address,
                        project_id=project_id,
                        chain_id=self.chain_id,
                        deployer=deployer,
                        transaction_from_address=create_transaction.from_address,
                        trace_creator=a_trace.from_address,
                        block_number=create_transaction.block_number,
                        block_timestamp=create_transaction.block_timestamp,
                        transaction_hash=create_transaction.hash,
                    )
                )
        return res

    def contract_create_contracts(self, project_id, deployer, filtered_trace_list: List[Trace]):
        res = []

        for a_trace in filtered_trace_list:
            create_transaction = self.transaction_map.get(a_trace.transaction_hash)
            if not create_transaction:
                # transaction failed
                continue
            if create_transaction.to_address in self.project_contracts[project_id]:
                res.append(
                    ProjectContractD(
                        address=a_trace.to_address,
                        project_id=project_id,
                        chain_id=self.chain_id,
                        deployer=deployer,
                        transaction_from_address=create_transaction.from_address,
                        trace_creator=a_trace.from_address,
                        block_number=create_transaction.block_number,
                        block_timestamp=create_transaction.block_timestamp,
                        transaction_hash=create_transaction.hash,
                    )
                )
        return res
