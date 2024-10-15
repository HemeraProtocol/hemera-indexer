import logging
from collections import defaultdict
from typing import List

from indexer.domain.block import Block
from indexer.domain.contract import Contract
from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob, FilterTransactionDataJob
from indexer.modules.custom.project_contracts.domain.project_contract_domain import ProjectContractD
from indexer.modules.custom.project_contracts.models.projects import AfProjects
from indexer.utils.abi import bytes_to_hex_str

logger = logging.getLogger(__name__)


class ExportProjectContractsJob(ExtensionJob):
    dependency_types = [Block, Transaction, Trace, Contract]
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
        self.trace_type_prefix = 'create'
        self.project_deployers = defaultdict(list)
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
        traces = self._data_buff[Trace.type()]
        filtered_trace = [trace for trace in traces if
                          trace.trace_type.startswith(self.trace_type_prefix) and trace.status == 1]
        contracts = self._data_buff[Contract.type()]

        res = []
        for project_id, deployers in self.project_deployers.items():
            project = self.project_map[project_id]
            self.current_project_id = project_id
            for deployer in deployers:
                tmp = []
                tmp.extend(self.list_pool_by_transaction_from(deployer, contracts, transactions))

                froms, ans = [deployer], []

                self.get_trace_from(froms, ans, project_id, contracts, transactions, filtered_trace)

                # this address is created by factory
                lis = self.list_created_pool_by_tx_from_and_to(deployer, self.common_factory, transactions, filtered_trace)
                ans.extend(lis)

                self.get_trace_from(lis, ans, project_id, contracts, transactions, filtered_trace)
                if project.address_type == 1:
                    ans.append(project.deployer)
                ans = list(set(ans))
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

    def read_configured_projects(self):
        with self.db_service.get_service_session() as session:
            query = session.query(AfProjects)
            result = query.all()
        for project in result:
            self.project_deployers[project.project_id].append(bytes_to_hex_str(project.deployer))
            self.project_map[project.project_id] = project

    def fetch_result(self, query):
        with self.db_service.get_service_session() as session:
            result = session.execute(query)
        return result

    def list_created_pool_by_tx_from_and_to(self, from_address, to_address, transactions, filtered_trace_lis) -> List[ProjectContractD]:
        """
        SELECT t.to_address
        FROM traces t
                 JOIN transactions tr ON t.transaction_hash = tr.hash
        WHERE tr.from_address = #{fromAddress}
          AND tr.to_address = #{toAddress}
          AND t.trace_type LIKE 'create%'
          AND t.status = 1;
        """
        transaction_hash_set = set([tnx.hash for tnx in transactions if tnx.from_address == from_address and tnx.to_address == to_address])
        res = [ProjectContractD(
            address=tra.to_address,
            project_id=self.current_project_id,
            chain_id=self.chain_id,
            deployer=self.current_deployer,
            transaction_from_address=self.transaction_map[tra.transaction_hash].from_address,
            trace_creator=tra.trace_creator,
            block_number=self.transaction_map[tra.transaction_hash].block_number,
            block_timestamp=self.transaction_map[tra.transaction_hash].block_timestamp,
            transaction_hash=tra.transaction_hash
        ) for tra in filtered_trace_lis if tra.transaction_hash in transaction_hash_set]
        return res

    def list_created_pool_by_transaction_from(self, project_id, from_address, filtered_trace_lis, transactions, project_contracts) -> List[ProjectContractD]:
        """
        SELECT t.to_address
        FROM traces t
        JOIN transactions tr ON t.transaction_hash = tr.hash
        LEFT JOIN protocol_contracts pc ON tr.to_address = pc.contract_address AND pc.protocol_id != #{protocolId}
        WHERE tr.from_address = #{address}
          AND pc.contract_address IS NULL
          AND t.trace_type LIKE 'create%'
          AND t.status = 1;
        """
        transaction_hash_set = [tra.hash for tra in transactions if tra.from_address == from_address]
        filtered_trace_lis = [tra for tra in filtered_trace_lis if tra.transaction_hash in transaction_hash_set]
        res = [ProjectContractD(
            address=tra.to_address,
            project_id=self.current_project_id,
            chain_id=self.chain_id,
            deployer=self.current_deployer,
            transaction_from_address=self.transaction_map[tra.transaction_hash].from_address,
            trace_creator=tra.trace_creator,
            block_number=self.transaction_map[tra.transaction_hash].block_number,
            block_timestamp=self.transaction_map[tra.transaction_hash].block_timestamp,
            transaction_hash=tra.transaction_hash
        ) for tra in filtered_trace_lis]
        return res

    def get_transaction_to_hash(self, address, transactions):
        """
        SELECT hash
        FROM transactions
        WHERE to_address = #{address}
        """
        transactions = [tra for tra in transactions if tra.to_address == address]
        res = list(set([tra.hash for tra in transactions]))
        return res

    def list_pool_by_transaction_from(self, address, contracts: List[Contract], transactions: List[Transaction]) -> List[ProjectContractD]:
        """
        SELECT t.address
        FROM contracts t JOIN transactions tr ON t.transaction_hash = tr.hash
        WHERE tr.from_address = #{address}
          AND tr.receipt_status = 1;
        """
        res = []
        filtered_transactions = set([tra.hash for tra in transactions if tra.from_address == address and tra.receipt])
        for contract in contracts:
            if contract.transaction_hash in filtered_transactions:
                res.append(ProjectContractD(
                        address=contract.address,
                        project_id=self.current_project_id,
                        chain_id=self.chain_id,
                        deployer=self.current_deployer,
                        transaction_from_address=self.transaction_map[contract.transaction_hash].from_address,
                        trace_creator=None,
                        block_number=self.transaction_map[contract.transaction_hash].block_number,
                        block_timestamp=self.transaction_map[contract.transaction_hash].block_timestamp,
                        transaction_hash=contract.transaction_hash
        ))
        return res

    def list_pool_by_trace_hash(self, tnx_hash_lis, filtered_trace):
        """
        SELECT to_address
        FROM traces WHERE
        transaction_hash IN
        <foreach item="item" collection="list" open="(" separator="," close=")">
            #{item}
        </foreach>
        AND trace_type LIKE 'create%' AND status = 1;
        """
        trace_lis = [tra for tra in filtered_trace if tra.transaction_hash in tnx_hash_lis]
        res = [tra.to_address for tra in trace_lis]
        return res

    def get_trace_from(self, froms: List[ProjectContractD], ans: List[str], project_id: str, contracts: List[Contract], transactions: List[Transaction], filtered_trace_lis):
        if not froms:
            return
        next_list = []
        count = 0
        for from_address in froms:
            from_address = from_address.address
            count += 1
            string_list = self.list_pool_by_transaction_from(from_address, contracts, transactions)

            if string_list:
                ans.extend(string_list)
                next_list.extend(string_list)

            transaction_from = self.list_created_pool_by_transaction_from(project_id, from_address, filtered_trace_lis, transactions, None)
            if transaction_from:
                ans.extend(transaction_from)
                next_list.extend(transaction_from)

        if next_list:
            self.get_trace_from(next_list, ans, project_id, contracts, transactions, filtered_trace_lis)
