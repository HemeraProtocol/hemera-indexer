from common.utils.abi_code_utils import Event


class IndexRecordEvent(Event):
    def __init__(self):
        super().__init__(
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "internalType": "uint256", "name": "chainId", "type": "uint256"},
                    {"indexed": False, "internalType": "uint256", "name": "startBlock", "type": "uint256"},
                    {"indexed": False, "internalType": "uint256", "name": "endBlock", "type": "uint256"},
                    {"indexed": False, "internalType": "bytes32", "name": "codeHash_", "type": "bytes32"},
                    {
                        "components": [
                            {"internalType": "bytes4", "name": "dataClass", "type": "bytes4"},
                            {"internalType": "uint256", "name": "count", "type": "uint256"},
                            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
                        ],
                        "indexed": False,
                        "internalType": "struct HemeraHistoryTransparency.IndexerOutput",
                        "name": "outputs",
                        "type": "tuple",
                    },
                ],
                "name": "indexRecord",
                "type": "event",
            }
        )
