import json
import logging
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from urllib.parse import urlparse

from kafka import KafkaProducer
from kafka.errors import KafkaError

from hemera.indexer.domains import Domain
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.exporters.base_exporter import BaseExporter
from hemera_udf.swap.domains.swap_event_domain import (
    FourMemeSwapEvent,
    UniswapV2SwapEvent,
    UniswapV3SwapEvent,
    UniswapV4SwapEvent,
)
from hemera_udf.token_holder_metrics.domains.metrics import TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD
from hemera_udf.token_price.domains import DexBlockTokenPrice

logger = logging.getLogger(__name__)
import os

chain_name = os.environ.get("CHAIN_NAME", "default")


class KafkaItemExporter(BaseExporter):
    def __init__(self, output, max_retries=5, ack_mode="all", timeout=30):
        """
        Initialize Kafka exporter with reliable delivery settings.

        Args:
            output: Kafka connection URL
            max_retries: Number of retry attempts for message delivery
            ack_mode: Acknowledgment mode ("all" for strongest guarantee)
            timeout: Timeout in seconds for message delivery confirmation
        """
        self.connection_url = self.get_connection_url(output)
        self.max_retries = max_retries
        self.timeout = timeout
        self.producer = None
        self._create_producer(ack_mode)

    def _create_producer(self, ack_mode):
        """Create Kafka producer with reliability settings."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.connection_url,
                security_protocol="SASL_SSL" if self.protocol == "kafka+ssl" else "SASL_PLAINTEXT",
                sasl_mechanism="PLAIN",
                sasl_plain_username=self.username,
                sasl_plain_password=self.password,
                ssl_cafile=None,
                # Reliability settings
                acks=ack_mode,  # Wait for all replicas to acknowledge
                retries=self.max_retries,  # Number of retries
                retry_backoff_ms=500,  # Backoff time between retries
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise

    def get_connection_url(self, output):
        """Parse and validate Kafka connection URL."""
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
        """Export multiple items to Kafka with delivery guarantees."""
        success_count = 0
        fail_count = 0

        for item in items:
            try:
                result = self.export_item(item)
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Failed to export item: {e}")
                fail_count += 1

        logger.info(f"Exported {success_count} items successfully, {fail_count} failed")
        return success_count, fail_count

    def export_item(self, item: Domain, **kwargs):
        """
        Export a single item to Kafka with guaranteed delivery.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False

        item = self.domain_mapping(item)
        if item is None:
            return False

        try:
            # Prepare the data
            data = {key: value for key, value in asdict(item).items() if value is not None}
            utc_now = datetime.now(timezone.utc)
            utc_timestamp = int(utc_now.timestamp())
            data["update_time"] = utc_timestamp
            encoded_data = json.dumps(data).encode("utf-8")

            # Send the message and wait for confirmation
            topic = item.type()
            if chain_name != "base":
                topic = f"{chain_name}_{topic}"

            future = self.producer.send(topic, value=encoded_data)

            # Block until the message is sent (or timeout)
            record_metadata = future.get(timeout=self.timeout)

            logger.debug(
                f"Message sent successfully to {topic} "
                f"[partition={record_metadata.partition}, offset={record_metadata.offset}]"
            )
            return True

        except KafkaError as ke:
            logger.error(f"Kafka error while exporting item: {ke}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while exporting item: {e}")
            return False

    def close(self):
        pass

    def domain_mapping(self, item):
        """Map domain objects for Kafka compatibility."""
        data = deepcopy(item)

        if isinstance(data, (TokenBalance, CurrentTokenBalance)):
            if data.token_id is None or data.token_id < 0:
                data.token_id = 0
            return data
        if isinstance(data, DexBlockTokenPrice):
            data.token_symbol = ""
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
                UniswapV4SwapEvent,
                FourMemeSwapEvent,
                ERC20TokenTransfer,
                TokenHolderMetricsCurrentD,
                TokenHolderMetricsHistoryD,
            ),
        ):
            return data

        return None
