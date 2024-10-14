import logging
from collections import defaultdict
from typing import List

from sqlalchemy import select, join, and_

from common.models.contracts import Contracts
from common.models.traces import Traces
from common.models.transactions import Transactions
from common.utils.exception_control import FastShutdownError
from indexer.domain.contract import Contract
from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.project_contracts.domain.project_contract_domain import ProjectContractD
from indexer.modules.custom.project_contracts.models.projects import AfProjects
from indexer.modules.custom.project_contracts.models.project_contract import AfProjectContracts

logger = logging.getLogger(__name__)


class ExportProjectContractsJob(FilterTransactionDataJob):
    # transaction with its logs
    dependency_types = [Transaction, Trace, Contract]
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
        self.common_factory = '0x4e59b44847b379578588920ca78fbf26c0b4956c'
        self.project_deployers = defaultdict(list)
        self.project_map = dict()

        self.env_check()
        self.read_configured_projects()

    def _collect(self, **kwargs):
        res = []
        for project_id, deployers in self.project_deployers.items():
            project = self.project_map[project_id]
            for deployer in deployers:
                froms, ans = [deployer], []
                self.get_trace_from(froms, ans, project_id)
                lis = self.list_created_pool_by_tx_from_and_to(deployer, self.common_factory)
                # 这些地址呢，就是通过factory创建的
                ans.extend(lis)
                self.get_trace_from(lis, ans, project_id)
                if project.address_type == 1:
                    ans.append(project.deployer)
                for s in ans:
                    res.append(ProjectContractD(
                        project_id=project_id,
                        chain_id=self.chain_id,
                        address=s,
                        deployer=deployer,
                        transaction_from_address=None,
                        trace_creator=None,
                        block_number=None,
                        block_timestamp=None,
                        transaction_hash=None
                    ))
        self._collect_items(ProjectContractD.type(), res)

    def env_check(self):
        # this job is strongly depended on database
        if not self.db_service:
            raise FastShutdownError("ExportProjectContractsJob need db_service, while its not available now")

    def read_configured_projects(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjects)
            result = query.all()
        for project in result:
            self.project_deployers[project.project_id].append(project.deployer)
            self.project_map[project.project_id] = project

    def fetch_result(self, query):
        with self.db_service.get_service_session() as session:
            result = session.execute(query)
        return result

    def list_created_pool_by_tx_from_and_to(self, from_address, to_address):
        query = (
            select(Traces.to_address)
            .select_from(
                join(Traces, Transactions, Traces.transaction_hash == Transactions.hash)
            )
            .where(
                and_(
                    Transactions.from_address == from_address,
                    Transactions.to_address == to_address,
                    Traces.trace_type.like('create%'),
                    Traces.status == 1
                )
            )
        )
        return self.fetch_result(query)

    def list_created_pool_by_transaction_from(self, project_id, from_address):
        query = (
            select(Traces.to_address)
            .select_from(
                join(Traces, Transactions, Traces.transaction_hash == Transactions.hash)
                .outerjoin(AfProjectContracts,
                           and_(
                               Transactions.to_address == AfProjects.contract_address,
                               AfProjectContracts.protocol_id != project_id
                           ))
            )
            .where(
                and_(
                    Transactions.from_address == from_address,
                    AfProjectContracts.contract_address == None,
                    Traces.trace_type.like('create%'),
                    Traces.status == 1
                )
            )
        )
        return self.fetch_result(query)

    def get_transaction_to_hash(self, address):
        with self.db_service.get_service_session() as session:
            result = session.query(Transaction).with_entities(Transaction.hash).filter(Transaction.to_address == address).all()
        return result

    def list_pool_by_transaction_from(self, address):
        query = (
            select(Contracts.address)
            .select_from(
                join(Contracts, Transactions, Contracts.transaction_hash == Transactions.hash)
            )
            .where(
                (Transactions.from_address == address) &
                (Transactions.receipt_status == 1)
            )
        )
        return self.fetch_result(query)


    def list_pool_by_trace_hash(self, transaction_hash_list):
        with self.db_service.get_service_session() as session:
            result = session.query(Trace).with_entities(Trace.to_address).filter((Trace.transaction_hash.in_(transaction_hash_list))).all()
        return result

    def get_trace_from(self, froms: List[str], ans: List[str], project_id: str):
        if not froms:
            return
        next_list = []
        count = 0
        for from_address in froms:
            count += 1
            string_list = self.list_pool_by_transaction_from(from_address)

            if string_list:
                ans.extend(string_list)
                next_list.extend(string_list)

            transaction_from = self.list_created_pool_by_transaction_from(from_address, project_id)
            if transaction_from:
                ans.extend(transaction_from)
                next_list.extend(transaction_from)

            if from_address == "0x56ad28ad449c7ceb805d92023aea986f8aae820f":
                transaction_to_hash = self.get_transaction_to_hash(from_address)
                if transaction_to_hash:
                    trace_hash = self.list_pool_by_trace_hash(transaction_to_hash)
                    if trace_hash:
                        ans.extend(trace_hash)
                        next_list.extend(trace_hash)

        if next_list:
            self.get_trace_from(next_list, ans, project_id)
