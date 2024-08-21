STAKED_PROTOCOL_DICT = {
    "0x3d9bcca8bc7d438a4c5171435f41a0af5d5e6083": "pump_btc",
}

STAKED_TOPIC0_DICT = {
    "0x3d9bcca8bc7d438a4c5171435f41a0af5d5e6083": "0xebedb8b3c678666e7f36970bc8f57abf6d8fa2e828c0da91ea5b75bf68ed101a",
}

STAKED_ABI_DICT = {
    "0xebedb8b3c678666e7f36970bc8f57abf6d8fa2e828c0da91ea5b75bf68ed101a":
        {
            "anonymous": False,
            "inputs": [
                {
                    "indexed": True,
                    "internalType": "address",
                    "name": "user",
                    "type": "address"
                },
                {
                    "indexed": False,
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                }
            ],
            "name": "Stake",
            "type": "event"
        }
}
