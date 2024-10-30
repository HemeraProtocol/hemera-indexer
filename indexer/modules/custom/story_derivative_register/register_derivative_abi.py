from indexer.utils.abi import Event

DERIVATIVE_REGISTERED_EVENT = Event(
	{
		"anonymous": False,
		"inputs": [
			{"indexed": True, "internalType": "address", "name": "caller", "type": "address"},
			{"indexed":True,"internalType":"address","name":"childIpId","type":"address"},
			{"indexed":False,"internalType":"uint256[]","name":"licenseTokenIds","type":"uint256[]"},
			{"indexed":False,"internalType":"address[]","name":"parentIpIds","type":"address[]"},
			{"indexed":False,"internalType":"uint256[]","name":"licenseTermsIds","type":"uint256[]"},
			{"indexed":False,"internalType":"address","name":"licenseTemplate","type":"address"}
		],
		"name": "DerivativeRegistered",
		"type": "event"
	}
)
