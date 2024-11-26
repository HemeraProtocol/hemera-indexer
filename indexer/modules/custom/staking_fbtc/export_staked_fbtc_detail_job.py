import ast
import configparser
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from common.utils.abi_code_utils import decode_log
from indexer.domains.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.staking_fbtc import utils
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import (
    StakedFBTCCurrentStatus,
    StakedFBTCDetail,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [StakedFBTCDetail, StakedFBTCCurrentStatus]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)
        self._service = kwargs["config"].get("db_service")
        self._current_holdings = utils.get_staked_fbtc_status(
            self._service, list(self.staked_abi_dict.keys()), int(kwargs["config"].get("start_block"))
        )

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            staked_protocol_dict_str = config.get(str(chain_id), "STAKED_PROTOCOL_DICT")
            self.staked_protocol_dict = ast.literal_eval(staked_protocol_dict_str)

            staked_topic0_dict_str = config.get(str(chain_id), "STAKED_TOPIC0_DICT")
            self.staked_topic0_dict = ast.literal_eval(staked_topic0_dict_str)

            staked_abi_dict_str = config.get(str(chain_id), "STAKED_ABI_DICT")
            self.staked_abi_dict = ast.literal_eval(staked_abi_dict_str)

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Error parsing configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=list(self.staked_abi_dict.keys())),
            ]
        )

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        staked_details, current_status_list, current_holdings = collect_detail(
            logs, self._current_holdings, self.staked_abi_dict, self.staked_protocol_dict
        )
        for data in staked_details:
            self._collect_item(StakedFBTCDetail.type(), data)
        for data in current_status_list:
            self._collect_item(StakedFBTCCurrentStatus.type(), data)
        self._current_holdings = current_holdings

    def _process(self, **kwargs):
        self._data_buff[StakedFBTCDetail.type()].sort(key=lambda x: x.block_number)
        self._data_buff[StakedFBTCCurrentStatus.type()].sort(key=lambda x: x.block_number)


def collect_detail(
    logs: List[Log],
    current_holdings: Dict[str, Dict[str, StakedFBTCCurrentStatus]],
    staked_abi_dict: Dict[str, Any],
    staked_protocol_dict: Dict[str, str],
) -> Tuple[List[StakedFBTCDetail], List[StakedFBTCCurrentStatus], Dict[str, Dict[str, StakedFBTCCurrentStatus]]]:
    current_status = defaultdict(
        lambda: defaultdict(
            lambda: StakedFBTCCurrentStatus(
                vault_address="",
                protocol_id="",
                wallet_address="",
                amount=0,
                changed_amount=0,
                block_number=0,
                block_timestamp=0,
            )
        )
    )
    for contract_address, wallet_dict in current_holdings.items():
        for wallet_address, status in wallet_dict.items():
            current_status[contract_address][wallet_address] = status

    logs_by_address = defaultdict(lambda: defaultdict(list))
    for log in logs:
        if log.topic0 in staked_abi_dict and log.address in staked_protocol_dict:
            logs_by_address[log.address][log.block_number].append(log)

    staked_details = []

    for address, blocks in logs_by_address.items():
        protocol_id = staked_protocol_dict[address]

        for block_number in sorted(blocks.keys()):
            block_logs = blocks[block_number]
            block_changes = defaultdict(int)
            block_timestamp = block_logs[0].block_timestamp

            for log in block_logs:
                decode_staked = decode_log(staked_abi_dict[log.topic0], log)
                wallet_address = decode_staked["user"]
                amount = decode_staked["amount"]
                block_changes[wallet_address] += amount

            for wallet_address, change in block_changes.items():
                current_amount = current_status[address][wallet_address].amount
                new_amount = current_amount + change

                current_status[address][wallet_address] = StakedFBTCCurrentStatus(
                    vault_address=address,
                    protocol_id=protocol_id,
                    wallet_address=wallet_address,
                    amount=new_amount,
                    changed_amount=change,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )

                staked_details.append(
                    StakedFBTCDetail(
                        vault_address=address,
                        protocol_id=protocol_id,
                        wallet_address=wallet_address,
                        amount=new_amount,
                        changed_amount=change,
                        block_number=block_number,
                        block_timestamp=block_timestamp,
                    )
                )

    current_status_list = [status for address_dict in current_status.values() for status in address_dict.values()]

    updated_current_holdings = {}
    for contract_address, wallet_dict in current_status.items():
        updated_current_holdings[contract_address] = {}
        for wallet_address, status in wallet_dict.items():
            updated_current_holdings[contract_address][wallet_address] = status

    return staked_details, current_status_list, updated_current_holdings
