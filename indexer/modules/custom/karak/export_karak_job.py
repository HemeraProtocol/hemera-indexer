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
from indexer.modules.custom.karak.karak_abi import DEPOSIT_EVENT, START_WITHDRAWAL_EVENT, FINISH_WITHDRAWAL_EVENT
from indexer.modules.custom.karak.karak_domain import (
    KarakDepositD,
    KarakStatWithdrawD,
    KarakFinishWithDrawD, KarakVaultTokenD,
)
from indexer.modules.custom.karak.models.af_karak_vault_token import AfKarakVaultToken
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs, \
    TransactionFilterByTransactionInfo, ToAddressSpecification
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)


class ExportKarakJob(FilterTransactionDataJob):
    # transaction with its logs
    dependency_types = [Transaction]
    output_types = [KarakDepositD, KarakStatWithdrawD, KarakFinishWithDrawD]
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
        self.token_vaults = dict()
        self.init_vaults()

    def init_vaults(self):
        # fetch from database
        if not self.db_service:
            return

        with self.db_service.get_service_session() as session:
            query = session.query(AfKarakVaultToken)
            result = query.all()

        for r in result:
            self.token_vaults['0x' + hex(r.token)] = '0x' + hex(r.vault)

    def get_filter(self):
        # deposit, startWithdraw, finishWithdraw
        topics = ["0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7", "0x6ee63f530864567ac8a1fcce5050111457154b213c6297ffc622603e8497f7b2", "0x486508c3c40ef7985dcc1f7d43acb1e77e0059505d1f0e6064674ca655a0c82f"]
        addresses = []
        return [
            TransactionFilterByTransactionInfo(ToAddressSpecification("0x54e44dbb92dba848ace27f44c0cb4268981ef1cc")),
        ]

    def discover_vaults(self, transactions: List[Transaction]):
        res = []
        for transaction in transactions:
            # deployVault
            if not transaction.input.startswith("0xf0edf6aa"):
                continue
            logs = transaction.receipt.logs
            vault = None
            for log in logs:
                if log.topic0 == "0x2cd7a531712f8899004c782d9607e0886d1dbc91bfac7be88dadf6750d9e1419" and log.address == "0x54e44dbb92dba848ace27f44c0cb4268981ef1cc":
                    vault = log.topic1
                    break
            dd = self.decode_data(["address", "string", "string", "uint8"], bytes.fromhex(transaction.input[2:])[4:])
            kvt = KarakVaultTokenD(
                vault=vault,
                token=dd[0],
                name=dd[1],
                symbol=dd[2],
                asset_type=dd[3],
            )
            self.token_vaults[kvt.token] = kvt.vault
            res.append(kvt)
        return res

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        new_vaults = self.discover_vaults(transactions)
        if new_vaults:
            self._collect_items(KarakVaultTokenD.type(), new_vaults)
        res = []

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if log.topic0 == "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7":
                    dl = decode_log(DEPOSIT_EVENT, log)
                    token = dl.get("token")
                    amount = dl.get("amount")
                    balance = dl.get("balance")

                    pass
                elif log.topic0 == "0x6ee63f530864567ac8a1fcce5050111457154b213c6297ffc622603e8497f7b2":
                    dl = decode_log(START_WITHDRAWAL_EVENT, log)
                    vault = dl.get("vault")
                    staker = dl.get("staker")
                    operator = dl.get("operator")
                    withdrawer = dl.get("withdrawer")
                    shares = dl.get("shares")

                elif log.topic0 == "0x486508c3c40ef7985dcc1f7d43acb1e77e0059505d1f0e6064674ca655a0c82f":
                    dl = decode_log(FINISH_WITHDRAWAL_EVENT, log)
                    vault = dl.get("vault")
                    staker = dl.get("staker")
                    operator = dl.get("operator")
                    withdrawer = dl.get("withdrawer")
                    shares = dl.get("shares")
                    withdrawroot = dl.get("withdrawRoot")


    @staticmethod
    def decode_data(decode_types, output: Decodable) -> Any:
        try:
            return decode(decode_types, output)
        except Exception as e:
            logger.error(e)
            return [None] * len(decode_types)

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