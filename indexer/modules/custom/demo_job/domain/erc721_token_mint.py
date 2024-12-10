#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class ERC721TokenMint(FilterData):
    address: str
    token_address: str
    token_id: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
