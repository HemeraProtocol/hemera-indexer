#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/23 13:31
# @Author  will
# @File  karak_conf.py.py
# @Brief
CHAIN_CONTRACT = {
    1: {
        "DEPOSIT": {
            # address is all vaults
            "topic": "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7",
        },
        "TRANSFER": {
            # address is all vaults
            "topic": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        },
        "START_WITHDRAW": {
            "address": "0xafa904152e04abff56701223118be2832a4449e0",
            "topic": "0x6ee63f530864567ac8a1fcce5050111457154b213c6297ffc622603e8497f7b2",
        },
        "FINISH_WITHDRAW": {
            "address": "0xafa904152e04abff56701223118be2832a4449e0",
            "topic": "0x486508c3c40ef7985dcc1f7d43acb1e77e0059505d1f0e6064674ca655a0c82f",
        },
        "NEW_VAULT": {
            "address": "0x54e44dbb92dba848ace27f44c0cb4268981ef1cc",
            "topic": "0x2cd7a531712f8899004c782d9607e0886d1dbc91bfac7be88dadf6750d9e1419",
            "starts_with": "0xf0edf6aa",
        },
        "VAULT_SUPERVISOR": "0x54e44dbb92dba848ace27f44c0cb4268981ef1cc",
    }
}
