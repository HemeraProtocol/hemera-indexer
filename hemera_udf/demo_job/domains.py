#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class ERC721TokenMint(Domain):
    address: str
    token_address: str
    token_id: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
