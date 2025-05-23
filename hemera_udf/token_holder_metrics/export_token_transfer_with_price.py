import logging
from dataclasses import asdict

from sortedcontainers import SortedDict
from sqlalchemy import text

from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_holder_metrics.domains.metrics import ERC20TokenTransferWithPriceD
from hemera_udf.token_price.domains import DexBlockTokenPrice
from hemera_udf.uniswap_v2.domains import UniswapV2SwapEvent
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import UniswapV3SwapEvent

logger = logging.getLogger(__name__)


class ExportTokenTransferWithPriceJob(ExtensionJob):
    dependency_types = [ERC20TokenTransfer, DexBlockTokenPrice, UniswapV2SwapEvent, UniswapV3SwapEvent, TokenBalance]
    output_types = [ERC20TokenTransferWithPriceD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        self.token_price_maps = None

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        self._init_history_token_prices(kwargs["start_block"])
        self._init_token_dex_prices_batch(kwargs["start_block"], kwargs["end_block"])
        transfers = self._data_buff[ERC20TokenTransfer.type()]
        token_balance = {}
        for balance in self._data_buff[TokenBalance.type()]:
            token_balance[f"{balance.token_address}_{balance.address}_{balance.block_number}"] = balance.balance

        swaps = self._data_buff[UniswapV2SwapEvent.type()] + self._data_buff[UniswapV3SwapEvent.type()]
        swap_txs = {swap.transaction_hash: swap for swap in swaps}

        to_export = []
        for transfer in transfers:
            swap = swap_txs.get(transfer.transaction_hash)
            is_swap = False
            if swap:
                if swap.sender == transfer.from_address:
                    is_swap = True
                elif (hasattr(swap, "to_address") and swap.to_address == transfer.from_address) or (
                    hasattr(swap, "recipient") and swap.recipient == transfer.from_address
                ):
                    is_swap = True

            decimals = 0
            token = self.tokens.get(transfer.token_address)
            if token:
                decimals = token["decimals"]

            price = self._get_token_dex_price(transfer.token_address, transfer.block_number)
            from_address_balance = token_balance.get(
                f"{transfer.token_address}_{transfer.from_address}_{transfer.block_number}", 0
            )
            to_address_balance = token_balance.get(
                f"{transfer.token_address}_{transfer.to_address}_{transfer.block_number}", 0
            )
            to_export.append(
                ERC20TokenTransferWithPriceD(
                    **asdict(transfer),
                    price=price,
                    is_swap=is_swap,
                    from_address_balance=from_address_balance,
                    to_address_balance=to_address_balance,
                    decimals=decimals,
                )
            )
        self._collect_items(ERC20TokenTransferWithPriceD.type(), to_export)
        self._update_history_token_prices()

    def _init_history_token_prices(self, start_block: int):
        if self.token_price_maps is not None:
            return
        session = self._service.get_service_session()
        token_blocks = session.execute(
            text(
                """
                SELECT token_address, block_number, token_price
                FROM (
                    SELECT token_address, block_number, token_price,
                           ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY block_number DESC) as rn
                    FROM af_dex_block_token_price
                    WHERE block_number < :start_block
                ) t
                WHERE rn = 1
            """
            ),
            {"start_block": start_block},
        ).fetchall()
        session.close()
        self.token_price_maps = {}
        for row in token_blocks:
            token_addr = bytes_to_hex_str(row[0])
            block_number = row[1]
            self.token_price_maps[token_addr] = SortedDict()
            self.token_price_maps[token_addr][block_number] = float(row[2])

    def _init_token_dex_prices_batch(self, start_block: int, end_block: int):

        price_sql = text(
            """
            SELECT token_address, block_number, token_price
            FROM af_dex_block_token_price
            WHERE block_number BETWEEN :min_block AND :max_block
            ORDER BY block_number
            """
        )

        session = self._service.get_service_session()
        prices = session.execute(price_sql, {"min_block": start_block, "max_block": end_block}).fetchall()
        session.close()

        for price_row in prices:
            token_addr = bytes_to_hex_str(price_row[0])
            if token_addr not in self.token_price_maps:
                self.token_price_maps[token_addr] = SortedDict()
            block_num = price_row[1]
            price = float(price_row[2])
            self.token_price_maps[token_addr][block_num] = price

    def _get_token_dex_price(self, token_addr: str, block_num: int):
        price_map = self.token_price_maps.get(token_addr)
        if not price_map:
            return 0.0

        keys = list(price_map.keys())
        idx = price_map.bisect_left(block_num)

        if idx == 0:
            return 0.0
        elif idx == len(keys):
            return price_map[keys[-1]]
        elif keys[idx] == block_num:
            return price_map[block_num]
        else:
            return price_map[keys[idx - 1]]

    def _update_history_token_prices(self):
        for token_addr, price_map in self.token_price_maps.items():
            if not price_map:
                continue
            latest_block = price_map.keys()[-1]
            latest_price = price_map[latest_block]

            # Clear all data and keep only the latest price
            price_map.clear()
            price_map[latest_block] = latest_price
