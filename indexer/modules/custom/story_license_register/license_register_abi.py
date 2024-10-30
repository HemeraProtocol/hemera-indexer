from indexer.utils.abi import Event

LICENSE_EVENT = Event(
    {
		"anonymous": False,
		"inputs": [
			{"indexed":True,"internalType":"uint256","name":"licenseTermsId","type":"uint256"},
            {"indexed":True,"internalType":"address","name":"licenseTemplate","type":"address"},
            {"indexed":False,"internalType":"bytes","name":"licenseTerms","type":"bytes"}
		],
		"name": "LicenseTermsRegistered",
		"type": "event",
	}
)
