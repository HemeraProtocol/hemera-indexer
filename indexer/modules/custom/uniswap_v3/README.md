## How to Index Data for Uniswap V3-Type Protocols

### 1. Configuration
In the `config.ini` file, configure the protocol information for your specific blockchain. Use the `chainId` as the key.

### 2. Verify ABI
Ensure that the ABI matches the Uniswap V3-type protocol you're working with. If it doesn't, update the ABI in the `constants` file.

### 3. Indexing Data
To start indexing the data, run the following command:
```bash
python hemera.py stream -pg postgresql://{db_user}:{db_password}@{db_url}:5432/{database} -p {chain_rpc} -s {start_block_number} -e {end_block_number} -o postgres -B 1000 -w 5 -b 100 -E {entity_type}
```
(you can add your {entity_type} in `enumeration/entity_type.py`)

### 4. Verify Data
To check the indexed data, run the API and call `localhost:8082/v1/uniswapv3/{wallet_address}`. This will retrieve the details of the tokens added by the user as liquidity in the Uniswap V3-type protocol.

