import logging
from collections import defaultdict
from typing import List

from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.domain.transaction import Transaction
from indexer.jobs.base_job import ExtensionJob
from indexer.modules.custom.project_contracts.domain.project_contract_domain import ProjectContractD
from indexer.modules.custom.project_contracts.models.project_contract import AfProjectContracts
from indexer.modules.custom.project_contracts.models.projects import AfProjects
from indexer.utils.abi import bytes_to_hex_str

logger = logging.getLogger(__name__)


class ExportProjectContractsJob(ExtensionJob):
    dependency_types = [Transaction, ContractInternalTransaction]
    output_types = [ProjectContractD]
    able_to_reorg = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db_service = kwargs["config"].get("db_service")
        self.chain_id = self._web3.eth.chain_id

        self.project_deployers = defaultdict(list)
        self.project_contracts = defaultdict(set)

        self.read_configured_projects()
        self.read_discovered_contracts()

    def _collect(self, **kwargs):
        transactions = self._data_buff[Transaction.type()]
        transactions = [
            a_transaction
            for a_transaction in transactions
            if a_transaction.receipt and a_transaction.receipt.status == 1
        ]
        contract_internal_transactions: List[ContractInternalTransaction] = self._data_buff[
            ContractInternalTransaction.type()
        ]
        contract_internal_transactions = [cit for cit in contract_internal_transactions if cit.is_contract_creation()]
        transaction_map = {tnx.hash: tnx for tnx in transactions}
        all_contracts = []
        for a_trace in contract_internal_transactions:
            create_transaction = transaction_map.get(a_trace.transaction_hash)
            if not create_transaction:
                continue
            all_contracts.append(
                ProjectContractD(
                    address=a_trace.to_address,
                    project_id=None,
                    chain_id=self.chain_id,
                    deployer=None,
                    transaction_from_address=create_transaction.from_address,
                    trace_creator=a_trace.from_address,
                    block_number=create_transaction.block_number,
                    block_timestamp=create_transaction.block_timestamp,
                    transaction_hash=create_transaction.hash,
                )
            )
        res = []
        for project_contract in all_contracts:
            for project_id, deployers in self.project_deployers.items():
                if self.direct_create_contracts(project_contract, set(deployers), transaction_map):
                    project_contract.project_id = project_id
                    res.append(project_contract)

                    break
                if self.contract_create_contracts(project_contract, project_id, transaction_map):
                    res.append(project_contract)
                    break
        self._collect_items(ProjectContractD.type(), res)
        # merge new contracts into exists
        for pc in res:
            self.project_contracts[pc.project_id].add(pc.address)

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

    def direct_create_contracts(self, project_contract: ProjectContractD, deployers: set, transaction_map) -> bool:
        create_transaction = transaction_map.get(project_contract.transaction_hash)
        if not create_transaction:
            return False
        if create_transaction.from_address in deployers:
            project_contract.deployer = create_transaction.from_address
            return True
        return False

    def contract_create_contracts(self, project_contract: ProjectContractD, project_id, transaction_map) -> bool:
        create_transaction = transaction_map.get(project_contract.transaction_hash)
        if not create_transaction:
            return False
        if create_transaction.to_address in self.project_contracts[project_id]:
            project_contract.project_id = project_id

            return True
        return False
