import os
import re
from configparser import ConfigParser
from dataclasses import dataclass, field
from enum import Enum, auto

from dataclass_wizard import YAMLWizard


@dataclass
class APIUrls(YAMLWizard):
    w3w_api_url: str = field(default="https://api.w3w.ai")


@dataclass
class TokenConfiguration(YAMLWizard):
    dashboard_token: str = field(default="ETH")
    native_token: str = field(default="ETH")
    gas_fee_token: str = field(default="ETH")


@dataclass
class CacheConfig(YAMLWizard):
    cache_type: str = field(default=None)
    cache_redis_host: str = field(default="127.0.0.1")
    cache_key_prefix: str = field(default="socialscan_api_ut")

    def get_cache_config(self, redis_db):
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
        else:
            return {
                "CACHE_TYPE": "SimpleCache",
                "DEBUG": True,
            }


@dataclass
class OpRollupDAConfig(YAMLWizard):
    da_type: str = field(default=None)
    plasma_api_endpoint: str = field(default=None)
    blob_scan_endpoint: str = field(default=None)


@dataclass
class L2Config(YAMLWizard):
    rollup_type: str = field(default=None)
    bridge_compatible: bool = field(default=False)
    withdrawal_expired_day: int = field(default=0)
    da_config: OpRollupDAConfig = field(default_factory=OpRollupDAConfig)


@dataclass
class DatabaseConfig(YAMLWizard):
    host: str = field(default=None)
    port: int = field(default=None)
    username: str = field(default=None)
    password: str = field(default=None)
    database: str = field(default=None)
    schema: str = field(default="public")

    def get_sql_alchemy_uri(self):
        user = self.username
        password = self.password
        host = self.host
        port = self.port
        database = self.database

        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


class APIModule(Enum):
    SOCIALSCAN = auto()
    EXPLORER = auto()
    L2_EXPLORER = auto()
    STATUS = auto()
    DEVELOPER = auto()
    CONTRACT = auto()
    INSCRIPTION = auto()
    CELESTIA = auto()
    USER_OPERATION = auto()


def parse_enum_list(enum_string):
    names = enum_string.split(",")
    enum_list = [APIModule[name.strip()] for name in names if name.strip() in APIModule.__members__]
    return enum_list


@dataclass
class AppConfig(YAMLWizard):
    api_modules: list = field(
        default_factory=lambda: [
            APIModule.EXPLORER,
            APIModule.DEVELOPER,
            APIModule.CONTRACT,
            APIModule.L2_EXPLORER,
            APIModule.USER_OPERATION,
        ]
    )
    env: str = field(default=None)
    chain: str = field(default=None)
    ens_service: str = field(default=None)
    contract_service: str = field(default=None)
    token_service: str = field(default=None)
    feature_flags: dict = field(default_factory=dict)
    l2_config: L2Config = field(default_factory=L2Config)
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    sql_alchemy_engine_options: dict = field(default_factory=dict)
    db_read_sql_alchemy_database_config: DatabaseConfig = field(default_factory=DatabaseConfig)
    db_write_sql_alchemy_database_config: DatabaseConfig = field(default_factory=DatabaseConfig)
    db_common_sql_alchemy_database_config: DatabaseConfig = field(default_factory=DatabaseConfig)
    sql_alchemy_database_engine_options: dict = field(
        default_factory=lambda: {
            "pool_size": 100,
            "max_overflow": 100,
        }
    )
    extra_config: dict = field(default_factory=dict)
    rpc: str = field(default="https://ethereum.publicnode.com")
    debug_rpc: str = field(default="https://ethereum.publicnode.com")
    token_configuration: TokenConfiguration = field(default_factory=TokenConfiguration)
    api_urls: APIUrls = field(default_factory=APIUrls)

    def get_default_token_image_url(self):
        return f"/images/empty-token-{self.chain}.png"

    def get_onchain_badge_config(self):
        if "on_chain_badge" in self.extra_config:
            return self.extra_config["ONCHAIN_BADGE_INFO"]

    @staticmethod
    def load_from_yaml_file(filename: str):
        return AppConfig.from_yaml_file(filename)

    @staticmethod
    def load_from_config_file(config: ConfigParser):
        db_creds = config["DB_CREDS"]
        block_chain = config["BLOCK_CHAIN"]
        settings = config["SETTINGS"]
        api_urls = config["API_URLS"]
        remote = config['REMOTE_SERVICE']
        extra_config = {}

        config_data = {
            "chain": block_chain["CHAIN"] or None,
            "extra_config": extra_config,
            "ens_service": remote.get("ENS_SERVICE") or None,
            "contract_service": remote.get("CONTRACT_SERVICE") or None,
            "token_service": remote.get("TOKEN_SERVICE") or None,
            "cache_config": CacheConfig(
                cache_type=settings.get("CACHE_TYPE") or "local",
                cache_redis_host=db_creds.get("REDIS_HOST") or "localhost",
                cache_key_prefix=f"socialscan_api",
            ),
            "db_read_sql_alchemy_database_config": DatabaseConfig(
                host=db_creds.get("HOST", "localhost"),
                port=int(db_creds.get("PORT", "5432")),
                username=db_creds.get("USER", "admin"),
                password=db_creds.get("PASSWD", "admin"),
                database=db_creds["DB_NAME"] or "default",
            ),
            "db_write_sql_alchemy_database_config": DatabaseConfig(
                host=db_creds["WRITE_HOST"],
                port=int(db_creds.get("PORT", "5432")),
                username=db_creds.get("USER", "admin"),
                password=db_creds.get("PASSWD", "admin"),
                database=db_creds["DB_NAME"] or "default",
            ),
            "db_common_sql_alchemy_database_config": DatabaseConfig(
                host=db_creds["COMMON_HOST"],
                port=int(db_creds.get("PORT", "5432")),
                username=db_creds.get("USER", "admin"),
                password=db_creds.get("PASSWD", "admin"),
                database=db_creds["DB_NAME"],
            ),
            "api_modules": (
                parse_enum_list(settings.get("API_MODULES") or "EXPLORER,DEVELOPER,CONTRACT,L2_EXPLORER")
                if block_chain.get("ROLLUP_TYPE")
                else parse_enum_list(settings.get("API_MODULES") or "EXPLORER,DEVELOPER,CONTRACT")
            ),
            "rpc": block_chain.get("RPC_ENDPOINT") or "https://ethereum.publicnode.com",
            "debug_rpc": block_chain.get("DEBUG_RPC_ENDPOINT") or "https://ethereum.publicnode.com",
            "token_configuration": TokenConfiguration(
                dashboard_token=block_chain.get("DASHBOARD_TOKEN") or "ETH",
                native_token=block_chain.get("NATIVE_TOKEN") or "ETH",
                gas_fee_token=block_chain.get("GAS_FEE_TOKEN") or "ETH",
            ),
            "api_urls": APIUrls(
                w3w_api_url=api_urls.get("W3W_API_HOST") or "https://api.w3w.ai",
            ),
        }
        if "ONCHAIN_BADGE" in config:
            config_data["extra_config"].update(config["ONCHAIN_BADGE"])

        return AppConfig(**config_data)
