import logging
from collections import defaultdict
from typing import Any, Dict, List

from eth_abi import decode
from eth_typing import Decodable
from sqlalchemy import func
from web3 import Web3

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.karak.karak_abi import FINISH_WITHDRAWAL_EVENT, START_WITHDRAWAL_EVENT, DEPOSIT_EVENT
from indexer.modules.custom.karak.karak_conf import CHAIN_CONTRACT
from indexer.modules.custom.karak.karak_domain import (
    KarakActionD,
    KarakAddressCurrentD,
    KarakVaultTokenD,
    karak_address_current_factory,
)
from indexer.modules.custom.karak.models.af_karak_address_current import AfKarakAddressCurrent
from indexer.modules.custom.karak.models.af_karak_vault_token import AfKarakVaultToken
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)


class ExportKarakJob(FilterTransactionDataJob):
    # transaction with its logs
    dependency_types = [Transaction]
    output_types = [KarakActionD, KarakVaultTokenD, KarakAddressCurrentD]
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
        self.chain_id = self._web3.eth.chain_id
        self.karak_conf = CHAIN_CONTRACT[self.chain_id]
        self.token_vault = dict()
        self.vault_token = dict()
        self.init_vaults()

    def init_vaults(self):
        # fetch from database
        if not self.db_service:
            return

        with self.db_service.get_service_session() as session:
            query = session.query(AfKarakVaultToken)
            result = query.all()

        for r in result:
            self.token_vault["0x" + r.token.hex()] = "0x" + r.vault.hex()
            self.vault_token["0x" + r.vault.hex()] = "0x" + r.token.hex()
        logging.info(f"init vaults with {len(self.token_vault)} tokens")

    def get_filter(self):
        # deposit, startWithdraw, finishWithdraw
        topics = []
        addresses = []
        for k, item in self.karak_conf.items():
            topics.append(item["topic"])
            addresses.append(item["address"])

        return [
            TransactionFilterByLogs(topics_filters=[TopicSpecification(topics=topics, addresses=addresses)]),
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
                if (
                    log.topic0 == self.karak_conf["NEW_VAULT"]["topic"]
                    and log.address == self.karak_conf["NEW_VAULT"]["address"]
                ):
                    vault = extract_eth_address(log.topic1)
                    break
            dd = self.decode_function(
                ["address", "string", "string", "uint8"], bytes.fromhex(transaction.input[2:])[4:]
            )
            kvt = KarakVaultTokenD(
                vault=vault,
                token=dd[0],
                name=dd[1],
                symbol=dd[2],
                asset_type=dd[3],
            )
            self.token_vault[kvt.token] = kvt.vault
            self.vault_token[kvt.vault] = kvt.token
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
            kad = None
            for log in logs:
                if (
                    log.topic0 == self.karak_conf["DEPOSIT"]["topic"]
                    and log.address == self.karak_conf["DEPOSIT"]["address"]
                ):
                    dl = decode_log(DEPOSIT_EVENT, log)
                    if transaction.input.startswith("0x47e7ef24"):
                        df = self.decode_function(["address", "uint256"], bytes.fromhex(transaction.input[2:])[4:])
                    else:
                        df = self.decode_function(
                            ["address", "uint256", "uint256"], bytes.fromhex(transaction.input[2:])[4:]
                        )
                    vault = df[0]
                    amount = df[1]
                    if not amount or not vault:
                        continue
                    staker = transaction.from_address
                    kad = KarakActionD(
                        transaction_hash=transaction.hash,
                        log_index=log.log_index,
                        transaction_index=transaction.transaction_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        method=transaction.input[0:10],
                        event_name="deposit",
                        topic0=log.topic0,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        vault=vault,
                        amount=amount,
                        staker=staker,
                    )
                    res.append(kad)
                elif (
                    log.topic0 == self.karak_conf["START_WITHDRAW"]["topic"]
                    and log.address == self.karak_conf["START_WITHDRAW"]["address"]
                ):
                    dl = decode_log(START_WITHDRAWAL_EVENT, log)
                    vault = dl.get("vault")
                    staker = dl.get("staker")
                    operator = dl.get("operator")
                    withdrawer = dl.get("withdrawer")
                    shares = dl.get("shares")
                    kad = KarakActionD(
                        transaction_hash=transaction.hash,
                        log_index=log.log_index,
                        transaction_index=transaction.transaction_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        method=transaction.input[0:10],
                        event_name="StartWithdrawal",
                        topic0=log.topic0,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        vault=vault,
                        staker=staker,
                        operator=operator,
                        withdrawer=withdrawer,
                        shares=shares,
                        amount=shares,
                    )
                    res.append(kad)

                elif (
                    log.topic0 == self.karak_conf["FINISH_WITHDRAW"]["topic"]
                    and log.address == self.karak_conf["FINISH_WITHDRAW"]["address"]
                ):
                    dl = decode_log(FINISH_WITHDRAWAL_EVENT, log)
                    vault = dl.get("vault")
                    staker = dl.get("staker")
                    operator = dl.get("operator")
                    withdrawer = dl.get("withdrawer")
                    shares = dl.get("shares")
                    withdrawroot = dl.get("withdrawRoot")
                    kad = KarakActionD(
                        transaction_hash=transaction.hash,
                        log_index=log.log_index,
                        transaction_index=transaction.transaction_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        method=transaction.input[0:10],
                        event_name="FinishedWithdrawal",
                        topic0=log.topic0,
                        from_address=transaction.from_address,
                        to_address=transaction.to_address,
                        vault=vault,
                        staker=staker,
                        operator=operator,
                        withdrawer=withdrawer,
                        shares=shares,
                        withdrawroot=withdrawroot,
                        amount=shares,
                    )
                    res.append(kad)
        for item in res:
            self._collect_item(item.type(), item)
        batch_result_dic = self.calculate_batch_result(res)
        exists_dic = self.get_existing_address_current(list(batch_result_dic.keys()))
        for address, outer_dic in batch_result_dic.items():
            for vault, kad in outer_dic.items():
                if address in exists_dic and vault in exists_dic[address]:
                    exists_kad = exists_dic[address][vault]
                    exists_kad.deposit_amount += kad.deposit_amount
                    exists_kad.start_withdraw_amount += kad.start_withdraw_amount
                    exists_kad.finish_withdraw_amount += kad.finish_withdraw_amount
                    self._collect_item(kad.type(), exists_kad)
                else:
                    self._collect_item(kad.type(), kad)

    @staticmethod
    def decode_function(decode_types, output: Decodable) -> Any:
        try:
            return decode(decode_types, output)
        except Exception as e:
            logger.error(e)
            return [None] * len(decode_types)

    def get_existing_address_current(self, addresses):
        if not self.db_service:
            return {}

        addresses = [ad[2:] for ad in addresses if ad and ad.startswith("0x")]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            query = session.query(AfKarakAddressCurrent).filter(
                func.encode(AfKarakAddressCurrent.address, "hex").in_(addresses)
            )
            result = query.all()
        lis = []
        for rr in result:
            lis.append(
                KarakAddressCurrentD(
                    address="0x" + rr.address.hex(),
                    vault="0x" + rr.vault.hex(),
                    deposit_amount=rr.deposit_amount,
                    start_withdraw_amount=rr.start_withdraw_amount,
                    finish_withdraw_amount=rr.finish_withdraw_amount,
                )
            )

        return create_nested_dict(lis)

    def calculate_batch_result(self, karak_actions: List[KarakActionD]) -> Any:
        def nested_dict():
            return defaultdict(karak_address_current_factory)

        res_d = defaultdict(nested_dict)
        for action in karak_actions:
            staker = action.staker
            vault = action.vault
            topic0 = action.topic0
            if topic0 == self.karak_conf["DEPOSIT"]["topic"]:
                res_d[staker][vault].address = staker
                res_d[staker][vault].vault = vault
                res_d[staker][vault].deposit_amount += action.amount
            elif topic0 == self.karak_conf["START_WITHDRAW"]["topic"]:
                res_d[staker][vault].address = staker
                res_d[staker][vault].vault = vault
                res_d[staker][vault].start_withdraw_amount += action.amount
            elif topic0 == self.karak_conf["FINISH_WITHDRAW"]["topic"]:
                res_d[staker][vault].address = staker
                res_d[staker][vault].vault = vault
                res_d[staker][vault].finish_withdraw_amount += action.amount
        return res_d


def create_nested_dict(data_list: List[KarakAddressCurrentD]) -> Dict[str, Dict[str, KarakAddressCurrentD]]:
    result = {}
    for item in data_list:
        if item.address and item.vault:
            if item.address not in result:
                result[item.address] = {}
            result[item.address][item.vault] = item
    return result


def extract_eth_address(input_string):
    hex_string = input_string.lower().replace("0x", "")

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()
