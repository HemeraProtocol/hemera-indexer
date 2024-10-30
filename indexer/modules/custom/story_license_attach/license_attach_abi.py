from indexer.utils.abi import Event

LICENSE_ATTACH_EVENT = Event(   
	{
		"anonymous": False,
		"inputs": [
			{"indexed":True,"internalType":"address","name":"caller","type":"address"},
			{"indexed":True,"internalType":"address","name":"ipId","type":"address"},
			{"indexed":False,"internalType":"address","name":"licenseTemplate","type":"address"},
			{"indexed":False,"internalType":"uint256","name":"licenseTermsId","type":"uint256"}
		],
		"name": "LicenseTermsAttached",
		"type": "event"
	}
)  