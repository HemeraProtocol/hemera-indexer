import os
from typing import Dict, List, Optional
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field

from hemera.common.enumeration.entity_type import calculate_entity_value, generate_entity_types


class TokenConfiguration(BaseModel):
    dashboard_token: str = Field(default="ETH")
    native_token: str = Field(default="ETH")
    gas_fee_token: str = Field(default="ETH")

    @classmethod
    def from_yaml(cls, data: dict) -> "TokenConfiguration":
        return cls(
            dashboard_token=data.get("dashboard_token", "ETH"),
            native_token=data.get("native_token", "ETH"),
            gas_fee_token=data.get("gas_fee_token", "ETH"),
        )


class CacheConfig(BaseModel):
    cache_type: Optional[str] = None
    cache_redis_host: str = Field(default="127.0.0.1")
    cache_key_prefix: str = Field(default="socialscan_api_ut")

    @classmethod
    def from_yaml(cls, data: dict) -> "CacheConfig":
        return cls(
            cache_type=data.get("cache_type"),
            cache_redis_host=data.get("cache_redis_host", "127.0.0.1"),
            cache_key_prefix=data.get("cache_key_prefix", "socialscan_api_ut"),
        )

    def get_cache_config(self, redis_db) -> Dict:
        if self.cache_type == "RedisCache":
            return {
                "CACHE_TYPE": "RedisCache",
                "CACHE_REDIS_HOST": redis_db.r,
                "CACHE_KEY_PREFIX": self.cache_key_prefix,
            }
        elif self.cache_type == "RedisClusterCache":
            return {
                "CACHE_TYPE": "RedisCache",
                "CACHE_REDIS_HOST": redis_db.r,
                "CACHE_KEY_PREFIX": self.cache_key_prefix,
            }
        return {
            "CACHE_TYPE": "SimpleCache",
            "DEBUG": True,
        }


class DatabaseConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    schema: str = Field(default="public")
    url: str = Field(default="")

    @classmethod
    def from_yaml(cls, data: dict) -> "DatabaseConfig":
        return cls(
            host=data.get("host"),
            port=data.get("port"),
            username=data.get("username"),
            password=data.get("password"),
            database=data.get("database"),
            schema=data.get("schema", "public"),
        )

    def get_sql_alchemy_uri(self) -> str:
        if self.url:
            return self.url
        else:
            return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @staticmethod
    def from_url(url: str) -> "DatabaseConfig":
        result = urlparse(url)
        return DatabaseConfig(
            host=result.hostname,
            port=result.port,
            username=result.username,
            password=result.password,
            database=result.path[1:],  # Remove leading '/'
            url=url,
        )


class Settings(BaseModel):
    udfs: List[str] = []
    chain: Optional[str] = None
    ens_service: Optional[str] = None
    contract_service: Optional[str] = None
    token_configuration: TokenConfiguration = Field(default_factory=TokenConfiguration)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    sql_alchemy_engine_options: Dict = Field(default_factory=dict)
    sql_alchemy_database_engine_options: Dict = Field(
        default_factory=lambda: {
            "pool_size": 100,
            "max_overflow": 100,
        }
    )
    rpc: str = Field(default="https://ethereum.publicnode.com")
    debug_rpc: str = Field(default="https://ethereum.publicnode.com")

    # constant
    MAX_INTERNAL_TRANSACTION: int = 10000
    MAX_TRANSACTION_WITH_CONDITION: int = 10000
    MAX_TRANSACTION: int = 10000
    PAGE_SIZE: int = 10

    class Config:
        env_file = ".env"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Settings":
        """Create settings from YAML file"""
        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f)

        settings = cls()

        # Load basic fields
        settings.udfs = config_data.get("udfs", [])
        settings.chain = config_data.get("chain")
        settings.ens_service = config_data.get("ens_service")
        settings.contract_service = config_data.get("contract_service")
        settings.rpc = config_data.get("rpc", "https://ethereum.publicnode.com")
        settings.debug_rpc = config_data.get("debug_rpc", "https://ethereum.publicnode.com")

        # Load nested configurations
        if "token_configuration" in config_data:
            settings.token_configuration = TokenConfiguration.from_yaml(config_data["token_configuration"])
        if "cache_config" in config_data:
            settings.cache_config = CacheConfig.from_yaml(config_data["cache_config"])
        if "sql_alchemy_database_engine_options" in config_data:
            settings.sql_alchemy_database_engine_options = config_data["sql_alchemy_database_engine_options"]

        return settings

    def update_from_env(self):
        """Update settings from environment variables"""
        self.udfs = generate_entity_types(calculate_entity_value(os.getenv("ENTITY_TYPES", "")))
        self.chain = os.getenv("CHAIN", self.chain)
        self.ens_service = os.getenv("ENS_SERVICE", self.ens_service)
        self.contract_service = os.getenv("CONTRACT_SERVICE", self.contract_service)

        if pool_size := os.getenv("SQL_POOL_SIZE"):
            self.sql_alchemy_database_engine_options["pool_size"] = int(pool_size)
        if max_overflow := os.getenv("SQL_MAX_OVERFLOW"):
            self.sql_alchemy_database_engine_options["max_overflow"] = int(max_overflow)

        self.rpc = os.getenv("PROVIDER_URI", self.rpc)
        self.debug_rpc = os.getenv("DEBUG_PROVIDER_URI", self.debug_rpc)

        # Update cache configuration
        if cache_type := os.getenv("CACHE_TYPE"):
            self.cache_config.cache_type = cache_type
            self.cache_config.cache_redis_host = os.getenv("REDIS_HOST", self.cache_config.cache_redis_host)

        # Update token configuration
        if dashboard_token := os.getenv("DASHBOARD_TOKEN"):
            self.token_configuration.dashboard_token = dashboard_token
        if native_token := os.getenv("NATIVE_TOKEN"):
            self.token_configuration.native_token = native_token
        if gas_fee_token := os.getenv("GAS_FEE_TOKEN"):
            self.token_configuration.gas_fee_token = gas_fee_token


def get_settings() -> Settings:
    """Factory function to create Settings instance with priority:
    1. Environment variables (highest priority)
    2. YAML file (if provided)
    3. Default values (lowest priority)
    """
    yaml_path = os.getenv("CONFIG_FILE")

    if yaml_path:
        settings = Settings.from_yaml(yaml_path)
    else:
        settings = Settings()

    # Environment variables override YAML settings
    settings.update_from_env()
    return settings


settings = get_settings()
