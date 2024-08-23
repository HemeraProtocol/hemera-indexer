import ast
import configparser
import logging
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import (
    TransferredFBTCCurrentStatus,
    TransferredFBTCDetail,
)
from indexer.modules.custom.staking_fbtc.models.feature_staked_fbtc_detail_status import FeatureStakedFBTCDetailStatus
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.TRANSFERRED_FBTC.value


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [TransferredFBTCDetail, TransferredFBTCCurrentStatus]
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
        self._service = (kwargs["config"].get("db_service"),)
        self._current_holdings = get_current_status(self._service, list(self._transferred_protocol_dict.keys()))

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._fbtc_address = config.get(str(chain_id), "FBTC_ADDRESS").lower()
            transferred_protocol_dict_str = config.get(str(chain_id), "TRANSFERRED_CONTRACTS_DICT")
            self._transferred_protocol_dict = ast.literal_eval(transferred_protocol_dict_str)

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._fbtc_address]),
            ]
        )

    def _collect(self, **kwargs):
        token_transfers = self._data_buff[ERC20TokenTransfer.type()]

        transferred_details, current_status_list, updated_current_holdings = process_token_transfers(
            token_transfers, self._current_holdings, self._transferred_protocol_dict, self._fbtc_address
        )

        for data in transferred_details:
            self._collect_item(TransferredFBTCDetail.type(), data)
        for data in current_status_list:
            self._collect_item(TransferredFBTCCurrentStatus.type(), data)
        self._current_holdings = updated_current_holdings

    def _process(self, **kwargs):
        self._data_buff[TransferredFBTCDetail.type()].sort(key=lambda x: x.block_number)
        self._data_buff[TransferredFBTCCurrentStatus.type()].sort(key=lambda x: x.block_number)


def get_current_status(db_service, transferred_contract_list):
    if not db_service:
        return {}
    bytea_address_list = []
    for address in transferred_contract_list:
        bytes_address = bytes.fromhex(address[2:])
        bytea_address_list.append(bytes_address)

    session = db_service[0].get_service_session()
    try:
        result = (
            session.query(FeatureStakedFBTCDetailStatus)
            .filter(FeatureStakedFBTCDetailStatus.contract_address.in_(bytea_address_list))
            .all()
        )
        transferred_fbtc_map = {}
        if result is not None:
            for item in result:
                item.contract_address = "0x" + item.contract_address.hex()
                item.wallet_address = "0x" + item.wallet_address.hex()
                transferred_fbtc_map[item.contract_address][item.wallet_address] = TransferredFBTCCurrentStatus(
                    contract_address=item.contract_address,
                    protocol_id=item.protocol_id,
                    wallet_address=item.wallet_address,
                    amount=item.amount,
                    block_number=item.item.block_number,
                    block_timestamp=item.item.block_timestamp,
                )

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return transferred_fbtc_map


def process_token_transfers(
    token_transfers: List[ERC20TokenTransfer],
    current_holdings: Dict[str, Dict[str, TransferredFBTCCurrentStatus]],
    transferred_protocol_dict: Dict[str, str],
    fbtc_address: str,
) -> Tuple[
    List[TransferredFBTCDetail], List[TransferredFBTCCurrentStatus], Dict[str, Dict[str, TransferredFBTCCurrentStatus]]
]:
    # Initialize current_status with existing holdings
    current_status = defaultdict(
        lambda: defaultdict(
            lambda: TransferredFBTCCurrentStatus(
                contract_address="", protocol_id="", wallet_address="", amount=0, block_number=0, block_timestamp=0
            )
        )
    )
    for contract_address, wallet_dict in current_holdings.items():
        for wallet_address, status in wallet_dict.items():
            current_status[contract_address][wallet_address] = status

    # Group transfers by block number
    transfers_by_block = defaultdict(list)
    for transfer in token_transfers:
        if transfer.token_address == fbtc_address:
            transfers_by_block[transfer.block_number].append(transfer)

    transferred_details = []

    # Process transfers block by block
    for block_number in sorted(transfers_by_block.keys()):
        block_transfers = transfers_by_block[block_number]
        block_changes = defaultdict(lambda: defaultdict(int))
        block_timestamp = block_transfers[0].block_timestamp

        # Accumulate changes within the block
        for entity in block_transfers:
            if entity.from_address in transferred_protocol_dict:
                from_contract_address = entity.from_address
                to_wallet_address = entity.to_address
                block_changes[from_contract_address][to_wallet_address] -= entity.value

            if entity.to_address in transferred_protocol_dict:
                to_contract_address = entity.to_address
                from_wallet_address = entity.from_address
                block_changes[to_contract_address][from_wallet_address] += entity.value

        # Apply accumulated changes and create TransferredFBTCDetail
        for contract_address, wallet_changes in block_changes.items():
            protocol_id = transferred_protocol_dict[contract_address]
            for wallet_address, change in wallet_changes.items():
                current_amount = current_status[contract_address][wallet_address].amount
                new_amount = current_amount + change

                current_status[contract_address][wallet_address] = TransferredFBTCCurrentStatus(
                    contract_address=contract_address,
                    protocol_id=protocol_id,
                    wallet_address=wallet_address,
                    amount=new_amount,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )

                transferred_details.append(
                    TransferredFBTCDetail(
                        contract_address=contract_address,
                        protocol_id=protocol_id,
                        wallet_address=wallet_address,
                        amount=new_amount,
                        block_number=block_number,
                        block_timestamp=block_timestamp,
                    )
                )

    # Convert current_status to list
    current_status_list = [status for address_dict in current_status.values() for status in address_dict.values()]

    # Update current_holdings with the latest status
    updated_current_holdings = {}
    for contract_address, wallet_dict in current_status.items():
        updated_current_holdings[contract_address] = {}
        for wallet_address, status in wallet_dict.items():
            updated_current_holdings[contract_address][wallet_address] = status

    return transferred_details, current_status_list, updated_current_holdings
