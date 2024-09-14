#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/4/16 19:48
# @Author  will
# @File  ens_conf.py
# @Brief

CONTRACT_NAME_MAP = {
    "0x283af0b28c62c092c9727f1ee09c02ca627eb7f5": "ENS: Old ETH Registrar Controller",
    "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85": "ENS: Base Registrar Implementation",
    "0x084b1c3c81545d370f3634392de611caabff8148": "ENS: Old Reverse Registrar 2",
    "0x4976fb03c32e5b8cfe2b6ccb31c09ba78ebaba41": "ENS: Public Resolver 2",
    "0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e": "ENS: Registry with Fallback",
    "0xa58e81fe9b61b5c3fe2afd33cf304c454abfc7cb": "ENS: Reverse Registrar",
    "0x314159265dd8dbb310642f98f50c066173c1259b": "ENS: Eth Name Service",
    "0xd4416b13d2b3a9abae7acd5d6c2bbdbe25686401": "ENS: Name Wrapper",
    "0xff252725f6122a92551a5fa9a6b6bf10eb0be035": "ENS: Bulk Renewal",
    "0x323a76393544d5ecca80cd6ef2a560c6a395b7e3": "ENS: Governance",
    "0xe65d8aaf34cb91087d1598e0a15b582f57f217d9": "ENS: Migration Subdomain Registrar",
    "0xc32659651d137a18b79925449722855aa327231d": "ENS: Subdomain Registrar",
    "0xdaaf96c344f63131acadd0ea35170e7892d3dfba": "ENS: Public Resolver 1",
    "0x9b6d20f524367d7e98ed849d37fc662402dca7fb": "ENS: Mapper",
    "0xf7c83bd0c50e7a72b55a39fe0dabf5e3a330d749": "ENS: Short Name Claims",
    "0x690f0581ececcf8389c223170778cd9d029606f2": "ENS: Cold Wallet",
    "0xd7a029db2585553978190db5e85ec724aa4df23f": "ENS: Token Timelock",
    "0xffc8ca4e83416b7e0443ff430cc245646434b647": "ENS: ENS Constitution Book Token",
    "0x911143d946ba5d467bfc476491fdb235fef4d667": "ENS: Multisig",
    "0xa2f428617a523837d4adc81c67a296d42fd95e86": "ENS: DNS Registrar",
    "0xfe89cc7abb2c4183683ab71653c4cdc9b02d44b7": "ENS: DAO Wallet",
    "0xa2c122be93b0074270ebee7f6b7292c7deb45047": "ENS: Default Reverse Resolver",
    "0xab528d626ec275e3fad363ff1393a41f581c5897": "ENS: Root",
    "0xb9d374d0fe3d8341155663fae31b7beae0ae233a": "ENS: Stable Price Oracle",
    "0xb1377e4f32e6746444970823d5506f98f5a04201": "ENS: Token Streaming Contract",
    "0x3671ae578e63fdf66ad4f3e12cc0c0d71ac7510c": "ENS: Reverse Records",
    "0x60c7c2a24b5e86c38639fd1586917a8fef66a56d": "ENS:  Registrar Migration",
    "0xc1735677a60884abbcf72295e88d47764beda282": "ENS: Offchain Resolver",
    "0x226159d592e2b063810a10ebf6dcbada94ed68b8": "ENS: Old Public Resolver 2",
    "0x9062c0a6dbd6108336bcbe4593a3d1ce05512069": "ENS: Old Reverse Registrar",
    "0x231b0ee14048e9dccd1d247744d114a4eb5e8e63": "ENS: Public Resolver",
    "0x253553366da8546fc250f225fe3d25d0c782303b": "ENS: ETH Registrar Controller",
    "0x00000000008794027c69c26d2a048dbec09de67c": "No Name Tag",
    "0x705bfbcfccde554e11df213bf6d463ea00dd57cc": "ETHBulkRegistrar",
    "0x1d6552e8f46fd509f3918a174fe62c34b42564ae": "ETHBulkRegistrarV1",
    "0xf5925e20e3f4002ba17130641a87f574c71a8b3c": "NOT Verified",
    "0x27c9b34eb43523447d3e1bcf26f009d814522687": "TransparentUpgradeableProxy",
    "0x5d81ce189bf5267e70fb555916ffbc3d4c7b2245": "EnsBatchRenew",
    "0x6109dd117aa5486605fc85e040ab00163a75c662": "RegistrarMigration",
    "0x6090a6e47849629b7245dfa1ca21d94cd15878ef": "ENS: Old Registrar",
    "0xfca3df2bcd9c3d594923ffae0f132bfa1e8297c4": "NOT Verified",
    "0xfc70fd608b3fb13a145e5d0e700b0fc00c10c5ef": "ENSVisionBulk",
}


ENS_BEGIN_BLOCK = 9380235
ENS_CONTRACT_CREATED_BLOCK = 3327417
BASE_NODE = "0x93cdeb708b7545dc668eb9280176169d1c33cfd8ed6f04690a0bcc88a93fc4ae"
REVERSE_BASE_NODE = "0x91d1777781884d03a6757a803996e38de2a42967fb37eeaca72729271025a9e2"
