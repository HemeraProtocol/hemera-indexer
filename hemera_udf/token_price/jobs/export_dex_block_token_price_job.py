import logging

import pandas as pd
from sqlalchemy import and_, func, or_

from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera.indexer.utils.collection_utils import distinct_collections_by_group
from hemera_udf.token_price.domains import DexBlockTokenPrice, DexBlockTokenPriceCurrent
from hemera_udf.uniswap_v2 import UniswapV2SwapEvent
from hemera_udf.uniswap_v3 import UniswapV3SwapEvent

logger = logging.getLogger(__name__)


class ExportDexBlockTokenPriceJob(ExtensionJob):
    dependency_types = [UniswapV2SwapEvent, UniswapV3SwapEvent, TokenBalance]

    output_types = [DexBlockTokenPrice, DexBlockTokenPriceCurrent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"].get("export_block_token_price_job", {})
        self.stable_tokens = config

        self.max_price = 200000
        self.max_market_cap = 1880666183880

    @staticmethod
    def dataclass_to_df(dataclass):
        dataclass_list = [dc.__dict__ for dc in dataclass]
        df = pd.DataFrame(dataclass_list)
        return df

    @staticmethod
    def process_swap_df(df):
        if df.empty:
            columns = ["block_number", "block_timestamp", "token_address", "token_price", "amount", "amount_usd"]
            return pd.DataFrame(columns=columns)

        token0_df = df[
            ["block_number", "block_timestamp", "token0_address", "token0_price", "amount0", "amount_usd"]
        ].rename(columns={"token0_address": "token_address", "token0_price": "token_price", "amount0": "amount"})
        token1_df = df[
            ["block_number", "block_timestamp", "token1_address", "token1_price", "amount1", "amount_usd"]
        ].rename(columns={"token1_address": "token_address", "token1_price": "token_price", "amount1": "amount"})
        return pd.concat([token0_df, token1_df], ignore_index=True)

    @staticmethod
    def extract_current_status(records, current_status_domain, keys):
        results = []
        last_records = distinct_collections_by_group(collections=records, group_by=keys, max_key="block_number")
        for last_record in last_records:
            record = current_status_domain(**vars(last_record))
            results.append(record)
        return results

    def process_token(self, df, token_prefix):
        # 获取列名
        address_col = f"{token_prefix}_address"
        price_col = f"{token_prefix}_price"
        dict_col = f"{token_prefix}_address_dict"
        decimals_col = f"{token_prefix}_decimals"
        supply_col = f"{token_prefix}_total_supply"
        # symbol_col = f'{token_prefix}_symbol'

        market_cap_col = "market_cap"

        # 提取 token 信息
        df[dict_col] = df[address_col].map(self.tokens)
        df[decimals_col] = df[dict_col].map(lambda x: x.get("decimals"))
        df[supply_col] = df[dict_col].map(lambda x: x.get("total_supply"))
        # df[symbol_col] = df[dict_col].map(lambda x: x.get('symbol'))

        # 计算市值
        df[market_cap_col] = df[price_col] * df[supply_col] / 10 ** df[decimals_col]
        return df[df[market_cap_col] < self.max_market_cap]

    def _process(self, **kwargs):
        token_balance_dict = {
            (tt.token_address, tt.address, tt.block_number): tt.balance
            for tt in self._data_buff[TokenBalance.type()]
            if tt.token_address in self.stable_tokens
        }

        uniswapv2_df_ = self.dataclass_to_df(self._data_buff[UniswapV2SwapEvent.type()])
        uniswapv2_df = self.process_uniswap_data(
            uniswapv2_df_, token_balance_dict, self.stable_tokens, self.max_price, self.process_token
        )
        uniswapv3_df_ = self.dataclass_to_df(self._data_buff[UniswapV3SwapEvent.type()])
        uniswapv3_df = self.process_uniswap_data(
            uniswapv3_df_, token_balance_dict, self.stable_tokens, self.max_price, self.process_token
        )

        processed_v2 = self.process_swap_df(uniswapv2_df)
        processed_v3 = self.process_swap_df(uniswapv3_df)

        combined_df = pd.concat([processed_v2, processed_v3], ignore_index=True)

        df_results = (
            combined_df.groupby(["token_address", "block_number", "block_timestamp"])
            .agg(
                token_price=("token_price", "median"),
                amount=("amount", lambda x: x.abs().sum()),
                amount_usd=("amount_usd", "sum"),
            )
            .reset_index()
        )

        records = df_results.to_dict("records")

        dex_block_token_price_list = []
        for record in records:

            # todo: improve
            token_dict = self.tokens.get(record.get("token_address"), {})
            token_symbol = token_dict.get("symbol")
            if not token_symbol:
                continue

            decimals = token_dict.get("decimals")
            record["amount"] = record.get("amount") / 10**decimals

            dex_block_token_price = DexBlockTokenPrice(**record, token_symbol=token_symbol, decimals=decimals)

            dex_block_token_price_list.append(dex_block_token_price)

        self._collect_domains(dex_block_token_price_list)

        current_results = self.extract_current_status(
            dex_block_token_price_list, DexBlockTokenPriceCurrent, ["token_address"]
        )
        self._collect_domains(current_results)
        pass

    def process_uniswap_data(self, df, token_balance_dict, stable_tokens, max_price, process_token_fn):
        df = df.dropna(subset=["token0_price"])
        df = df[df["token0_price"] < max_price]
        df = df[df["token1_price"] < max_price]

        df = process_token_fn(df, "token0")
        df = process_token_fn(df, "token1")

        df["stable_token_address_position"] = df.apply(lambda x: 0 if x.token0_address in stable_tokens else 1, axis=1)

        df["stable_token_symbol"] = df.apply(
            lambda x: stable_tokens.get(x.token0_address) or stable_tokens.get(x.token1_address), axis=1
        )

        df["stable_token_balance_limit"] = df.apply(lambda x: 0.001 if x.stable_token_symbol == "ETH" else 10, axis=1)

        # get stable_balance_raw
        df["token_balance_raw"] = df.apply(
            lambda x: token_balance_dict.get((x.token0_address, x.pool_address, x.block_number))
            or token_balance_dict.get((x.token1_address, x.pool_address, x.block_number)),
            axis=1,
        )

        df = df.dropna(subset=["token_balance_raw"])

        df["stable_balance"] = df.apply(
            lambda x: x.token_balance_raw
            / 10 ** (x.token1_decimals if x.stable_token_address_position else x.token0_decimals),
            axis=1,
        )

        df = df[df["stable_balance"] > df["stable_token_balance_limit"]]

        return df

    def _get_current_holdings(self, tokens, block_number):
        session = self._service.get_service_session()

        conditions = [
            and_(
                DexBlockTokenPrice.token_address == hex_str_to_bytes(token),
            ).self_group()  # need to group for one combination
            for token in tokens
        ]

        windowed_block_number = func.row_number().over(
            partition_by=(DexBlockTokenPrice.token_address,),
            order_by=DexBlockTokenPrice.block_number.desc(),
        )

        combined_conditions = or_(*conditions)

        subquery = (
            session.query(DexBlockTokenPrice, windowed_block_number.label("row_number"))
            .filter(combined_conditions, DexBlockTokenPrice.block_number < block_number)
            .subquery()
        )

        query = session.query(subquery).filter(subquery.c.row_number == 1)

        results = query.all()

        pre_prices_dict = {}
        for record in results:
            token_address = bytes_to_hex_str(record.token_address)
            pre_prices_dict[token_address] = record.token_price
        session.close()

        return pre_prices_dict
