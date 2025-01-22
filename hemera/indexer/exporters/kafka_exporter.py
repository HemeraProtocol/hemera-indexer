import json
import logging
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from urllib.parse import urlparse

from kafka import KafkaProducer

from hemera.indexer.domains import Domain
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.exporters.base_exporter import BaseExporter
from hemera_udf.token_holder_metrics.domains.metrics import TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD
from hemera_udf.token_price.domains import DexBlockTokenPriceCurrent
from hemera_udf.uniswap_v2 import UniswapV2SwapEvent
from hemera_udf.uniswap_v3 import UniswapV3SwapEvent

logger = logging.getLogger(__name__)


class KafkaItemExporter(BaseExporter):
    def __init__(self, output):
        self.connection_url = self.get_connection_url(output)
        self.producer = KafkaProducer(
            bootstrap_servers=self.connection_url,
            security_protocol="SASL_SSL" if self.protocol == "kafka+ssl" else "SASL_PLAINTEXT",
            sasl_mechanism="PLAIN",
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
            ssl_cafile=None,
        )

    def get_connection_url(self, output):
        try:
            parsed_url = urlparse(output)
            if parsed_url.scheme not in ["kafka", "kafka+ssl"]:
                raise ValueError('Invalid scheme in kafka URL. Use "kafka" or "kafka+ssl".')

            connection_url = parsed_url.hostname + ":" + str(parsed_url.port)
            self.username = parsed_url.username
            self.password = parsed_url.password
            self.protocol = parsed_url.scheme
            return connection_url
        except Exception as e:
            raise ValueError(f"Invalid kafka output param: {output}. Error: {e}")

    def open(self):
        pass

    def export_items(self, items, **kwargs):
        for item in items:
            self.export_item(item)

    def export_item(self, item: Domain, **kwargs):
        item = self.domain_mapping(item)
        if item is None:
            return
        data = {key: value for key, value in asdict(item).items() if value is not None}
        utc_now = datetime.now(timezone.utc)
        utc_timestamp = int(utc_now.timestamp())
        data["update_time"] = utc_timestamp
        data = json.dumps(data).encode("utf-8")
        self.producer.send(item.type(), value=data)

    def close(self):
        pass

    def domain_mapping(self, item):
        data = deepcopy(item)

        if isinstance(data, (TokenBalance, CurrentTokenBalance)):
            if data.token_id is None or data.token_id < 0:
                data.token_id = 0
            return data
        if isinstance(data, (TokenHolderMetricsHistoryD, TokenHolderMetricsCurrentD)):
            if data.current_balance:
                data.current_balance = int(data.current_balance)
            if data.max_balance:
                data.max_balance = int(data.max_balance)
            if data.total_buy_amount:
                data.total_buy_amount = int(data.total_buy_amount)
            if data.total_sell_amount:
                data.total_sell_amount = int(data.total_sell_amount)
            if data.swap_buy_amount:
                data.swap_buy_amount = int(data.swap_buy_amount)
            if data.swap_sell_amount:
                data.swap_sell_amount = int(data.swap_sell_amount)
            return data
        if isinstance(
            data,
            (
                UniswapV2SwapEvent,
                UniswapV3SwapEvent,
                ERC20TokenTransfer,
                DexBlockTokenPriceCurrent,
                Log,
                TokenHolderMetricsCurrentD,
                TokenHolderMetricsHistoryD,
            ),
        ):
            return data

        return None
