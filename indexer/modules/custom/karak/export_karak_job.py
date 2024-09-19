import logging
from collections import defaultdict
from typing import List, Any

from eth_abi import abi, decode
from eth_typing import Decodable
from sqlalchemy import func
from web3 import Web3

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.karak.karak_domain import (
    DepositD,
    StatWithdrawD,
    FinishWithDrawD,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs, \
    TransactionFilterByTransactionInfo, ToAddressSpecification

logger = logging.getLogger(__name__)


class SampleJob(FilterTransactionDataJob):
    # transaction with its logs
    dependency_types = [Transaction]
    output_types = [DepositD, StatWithdrawD, FinishWithDrawD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )

        self._is_batch = kwargs["batch_size"] > 1
        self.db_service = kwargs["config"].get("db_service")
        self.contract_address = "0xdac17f958d2ee523a2206206994597c13d831ec7"

    def get_filter(self):
        # deposit, startWithdraw, finishWithdraw
        topics = ["0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7", "0x6ee63f530864567ac8a1fcce5050111457154b213c6297ffc622603e8497f7b2", "0x486508c3c40ef7985dcc1f7d43acb1e77e0059505d1f0e6064674ca655a0c82f"]
        addresses = []
        return [
            TransactionFilterByTransactionInfo(ToAddressSpecification("0x54e44dbb92dba848ace27f44c0cb4268981ef1cc")),
        ]

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        res = []

        for transaction in transactions:
            if transaction.input.startswith("0x0efe6a8b"):
                dd = self.decode_data(["address", "uint256", "uint256"], bytes.fromhex(transaction.input[2:])[4:])
                address = dd[0]
                amount = dd[1]
                minSharesOut = dd[2]
                res.append(DepositD(

                ))

    @staticmethod
    def decode_data(decode_types, output: Decodable) -> Any:
        return decode(decode_types, output)

    # def get_existing_transfers(self, addresses):
    #     if not self.db_service:
    #         return {}
    #     addresses = [ad[2:] for ad in addresses if ad.startswith("0x")]
    #
    #     with self.db_service.get_service_session() as session:
    #         query = session.query(SampleAddressCurrent).filter(
    #             func.encode(SampleAddressCurrent.address, "hex").in_(addresses)
    #         )
    #         result = query.all()
    #
    #     return {
    #         f"{'0x' + row.address.hex()}": SampleAddressCurrentD(
    #             address=row.address,
    #             transaction_count=row.transaction_count,
    #             transfer_from_count=row.transfer_from_count,
    #             transfer_from_value=row.transfer_from_value,
    #             transfer_to_count=row.transfer_to_count,
    #             transfer_to_value=row.transfer_to_value,
    #             block_number=row.block_number,
    #         )
    #         for row in result
    #     }


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()