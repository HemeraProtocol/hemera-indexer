#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/20 15:29
# @Author  ideal93
# @File  address_enricher.py
# @Brief
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlmodel import Session

from hemera.app.api.routes.helper.contract import _get_contracts_by_addresses
from hemera.app.api.routes.helper.format import format_coin_value, format_dollar_value
from hemera.app.api.routes.helper.token import TokenInfo, get_coin_prices, get_token_map
from hemera.common.utils.format_utils import bytes_to_hex_str


class ExtraInfo(BaseModel):
    ens: Optional[str] = None
    tvl: Optional[float] = None


class Address(BaseModel):
    address: str = ""
    is_contract: bool = False
    name: Optional[str] = None
    extra_info: ExtraInfo = ExtraInfo()


class AddressEnricherServiceType(Enum):
    ENS = "ens"
    CONTRACT = "contract"


class EnricherType(Enum):
    ADDRESS = "address"
    COIN_VALUE = "coin_value"
    COIN_PRICE = "coin_price"
    TOKEN_INFO = "token_info"
    TOKEN_VALUE = "token_value"


# Contract
# ENS(Service)
# Contract(Service)


class AddressEnricher:
    """Class to enrich address data with additional information"""

    def __init__(self, services_list: List[AddressEnricherServiceType] = []):
        self.services_list = services_list
        self.coin_decimals = 18

    def get_address(self, session: Session, addresses: set[str]) -> Dict[str, Address]:
        enriched_address_dict = {address: Address(address=address) for address in addresses}
        contracts = _get_contracts_by_addresses(session, list(addresses))
        contracts_dict = {bytes_to_hex_str(contract.address): contract for contract in contracts}

        for address in enriched_address_dict:
            if address in contracts_dict:
                enriched_address_dict[address].is_contract = True
                enriched_address_dict[address].name = contracts_dict[address].name

        return enriched_address_dict

    def get_token_address(self, session: Session, addresses: set[str]) -> Dict[str, TokenInfo]:
        return get_token_map(session, list(addresses))

    def get_coin_price(self, session: Session, block_dates: set[datetime]) -> Dict[datetime, float]:
        prices = get_coin_prices(session, list(block_dates))
        return {price.block_date: price.price for price in prices}

    def enrich(
        self, items: List[Dict[str, Any]], fields_mapper: Dict[EnricherType, Dict[str, str]], session: Session
    ) -> List[Dict[str, Any]]:

        for enricher_type in fields_mapper:
            if enricher_type == EnricherType.ADDRESS:
                items = self.enrich_address(items, fields_mapper[enricher_type], session)
            elif enricher_type == EnricherType.COIN_VALUE:
                items = self.enrich_coin_value(items, fields_mapper[enricher_type])
            elif enricher_type == EnricherType.COIN_PRICE:
                items = self.enrich_coin_price(items, fields_mapper[enricher_type], session)
            elif enricher_type == EnricherType.TOKEN_INFO:
                items = self.enrich_token_info(items, fields_mapper[enricher_type], session)
            elif enricher_type == EnricherType.TOKEN_VALUE:
                items = self.enrich_token_value(items, fields_mapper[enricher_type])
            else:
                pass
        return items

    def enrich_address(
        self, items: List[Dict[str, Any]], fields_mapper: Dict[str, str], session: Session
    ) -> List[Dict[str, Any]]:
        addresses = set()
        for item in items:
            for field in fields_mapper:
                addresses.add(item[field])

        enriched_address_dict = self.get_address(session, addresses)

        enriched_items = []
        for item in items:
            for field in fields_mapper:
                item[fields_mapper[field]] = enriched_address_dict.get(item[field])
            enriched_items.append(item)
        return enriched_items

    def enrich_coin_value(self, items: List[Dict[str, Any]], fields_mapper: Dict[str, str]) -> List[Dict[str, Any]]:
        for item in items:
            for field in fields_mapper:
                item[fields_mapper[field]] = format_coin_value(item[field])
        return items

    def enrich_coin_price(
        self, items: List[Dict[str, Any]], fields_mapper: Dict[str, str], session: Session
    ) -> List[Dict[str, Any]]:
        block_dates = set()
        for item in items:
            block_dates.add(item["block_timestamp"].replace(second=0, microsecond=0))
        price_map = self.get_coin_price(session, block_dates)

        for item in items:
            coin_price = price_map.get(item["block_timestamp"].replace(second=0, microsecond=0), 0.0)
            for field in fields_mapper:
                item[fields_mapper[field]] = format_dollar_value(coin_price * float(item[field]))
        return items

    def enrich_token_info(
        self, items: List[Dict[str, Any]], fields_mapper: Dict[str, str], session: Session
    ) -> List[Dict[str, Any]]:
        addresses = set()
        for item in items:
            for field in fields_mapper:
                addresses.add(item[field])

        token_info_dict = self.get_token_address(session, addresses)

        enriched_items = []
        for item in items:
            for field in fields_mapper:
                item[fields_mapper[field]] = token_info_dict.get(item[field])
            enriched_items.append(item)
        return enriched_items

    def enrich_token_value(self, items: List[Dict[str, Any]], fields_mapper: Dict[str, str]) -> List[Dict[str, Any]]:
        for item in items:
            for field in fields_mapper:
                item[fields_mapper[field]] = format_coin_value(
                    item[field], (item.get("token_info").decimals if item.get("token_info") else 18) or 18
                )
        return items


class EnricherManager:
    _instance = None
    _enricher = None

    @classmethod
    def get_instance(cls) -> "EnricherManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_enricher(self) -> AddressEnricher:
        if self._enricher is None:
            self._enricher = AddressEnricher()
        return self._enricher
