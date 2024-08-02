<h1>Hemera Indexer</h1>
<p>By Hemera Protocol</p>
<p></p>

> [!NOTE]
> The Hemera Indexer is a work-in-progress project. If you need to use it in production, please consult the Hemera Team first.

## About Hemera Protocol

Hemera Protocol is a decentralized, account-centric programmable indexing network created to function as a public goods data infrastructure, enhancing the capabilities of data networks in web3. This platform supports many web3 applications, from straightforward to intricate, such as blockchain explorers, on-chain asset portfolios, social graphs, zero-knowledge (ZK) coprocessors, community quality auditing, and web3 identities. All these can benefit from or be built on top of Hemera.

## About Hemera Indexer

As the foundation of the Hemera Protocol, the blockchain indexer plays a crucial role. It is the primary component that enables efficient and organized access to blockchain data.
Initially inspired by open-source projects like Ethereum ETL, we expanded its capabilities as the Ethereum ecosystem evolved, with the emergence of more Layer 2 chains and new ERC standards. Recognizing the need for a robust solution, we decided to develop our own indexer as the first step in building the Hemera Protocol Network.
As of July 5, 2024, the initial open-source version of the Hemera Indexer offers comprehensive functionality, allowing for the indexing of any EVM-compatible chains and providing all necessary data for a basic blockchain explorer. In the coming weeks, we plan to incorporate additional features from our in-house version into the open-source version.

## Features Offered

##### Export the following entities

- Blocks
- Transactions
- Logs
- ERC20 / ERC721 / ERC1155 tokens
- ERC20 / ERC721 / ERC1155 Token transfers
- ERC20 / ERC721 / ERC1155 Token balance & holders
- Contracts
- Traces / Internal transactions
- L1 -> L2 Transactions (Coming Soon)
- L2 -> L1 Transactions (Coming Soon)
- Rollup Batches (Coming Soon)
- DA Transactions (Coming Soon)
- User Operations (Coming Soon)

##### Into the following formats

- Postgresql SQL
- JSONL
- CSV

##### Additional features

- Ability to select arbitrary block ranges for more flexible data indexing
- Option to choose any entities for targeted data extraction
- Automated reorg detection process to ensure data consistency and integrity

## Contents

<!-- TOC -->

- [Install and Run Hemera Indexer](#install-and-run-hemera-indexer)
  - [Prerequisites](#prerequisites)
  - [Hardware Requirements](#hardware-requirements)
  - [Run Hemera Indexer](#run-hemera-indexer)
    - [Run In Docker](#run-in-docker)
    - [Run From Source Code](#run-from-source-code)
- [Configure Hemera Indexer](#configure-hemera-indexer)
  - [Parameters](#parameters)
  - [Export Result](#export-result)
  <!-- TOC -->

## Install and Run Hemera Indexer

### Prerequisites

- VM Instance (or your local machine)
- RPC Node of your EVM-compatible blockchain

### Hardware Requirements

We recommend you have this configuration to run Hemera Indexer:

- 4-Core CPU
- at least 8 GB RAM
- an SSD drive with enough space left

#### Disk Usage

Based on the 2024 Ethereum, every 25k blocks, which is approximately 4.5 million transactions, consumes disk size as below

- 9GB PostgreSQL database
- 9.3GB CSV file, if you opt for the CSVV export.
- 15GB JSON file, if you opt for the JSON export
  That is about 35GB for every 25k blocks, for every 100k blocks, we recommend at least 150 GB for every 100k eth blocks.

#### Use VM From Cloud Services

If you don't have a VM in place, you can create VMs from cloud providers.
[Create an AWS EC2 Instance](AWS.md)

#### RPC Usage

The Indexer will consume a large number of RPC requests. Make sure you have a robust and fast RPC endpoint. Most of the time, the RPC endpoint will be the bottleneck for the indexer.

### Clone the Repository

```bash
git clone https://github.com/HemeraProtocol/hemera-indexer.git
or
git clone git@github.com:HemeraProtocol/hemera-indexer.git
```

### Run Hemera Indexer

We recommend running from docker containers using the provided `docker-compose.yaml` .
If you prefer running from source code, please check out [Run From Source Code](#run-from-source-code).

### Run In Docker

#### Install Docker & Docker Compose

If you have trouble running the following commands, consider referring to
the [official docker installation guide](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)
for the latest instructions.

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

```bash
# Install docker and docker compose
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

#### Run the Docker Compose

```bash
cd hemera-indexer
cd docker-compose
```

Alternatively, you might want to edit environment variables in `docker-compose.yaml`. Please check
out [configuration manual](#configure-hemera-indexer) on how to configure the environment variables.

```bash
vim docker-compose.yaml
```

Now, run the following command to spin up the containers.

```bash
sudo docker compose up
```

You should be able to see similar logs from your console that indicate Hemera Indexer is running properly.

```
[+] Running 2/0
 ✔ Container postgresql  Created                                                                                                                0.0s
 ✔ Container hemera      Created                                                                                                                0.0s
Attaching to hemera, postgresql
postgresql  |
postgresql  | PostgreSQL Database directory appears to contain a database; Skipping initialization
postgresql  |
postgresql  | 2024-06-24 08:18:48.547 UTC [1] LOG:  starting PostgreSQL 15.7 (Debian 15.7-1.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
postgresql  | 2024-06-24 08:18:48.548 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
postgresql  | 2024-06-24 08:18:48.549 UTC [1] LOG:  listening on IPv6 address "::", port 5432
postgresql  | 2024-06-24 08:18:48.554 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
postgresql  | 2024-06-24 08:18:48.564 UTC [27] LOG:  database system was shut down at 2024-06-24 06:44:23 UTC
postgresql  | 2024-06-24 08:18:48.575 UTC [1] LOG:  database system is ready to accept connections
hemera      | 2024-06-24 08:18:54,953 - root [INFO] - Using provider https://eth.llamarpc.com
hemera      | 2024-06-24 08:18:54,953 - root [INFO] - Using debug provider https://eth.llamarpc.com
hemera      | 2024-06-24 08:18:55,229 - alembic.runtime.migration [INFO] - Context impl PostgresqlImpl.
hemera      | 2024-06-24 08:18:55,230 - alembic.runtime.migration [INFO] - Will assume transactional DDL.
hemera      | 2024-06-24 08:18:55,278 - alembic.runtime.migration [INFO] - Context impl PostgresqlImpl.
hemera      | 2024-06-24 08:18:55,278 - alembic.runtime.migration [INFO] - Will assume transactional DDL.
hemera      | 2024-06-24 08:18:56,169 - root [INFO] - Current block 20160303, target block 20137200, last synced block 20137199, blocks to sync 1
hemera      | 2024-06-24 08:18:56,170 - ProgressLogger [INFO] - Started work. Items to process: 1.
hemera      | 2024-06-24 08:18:57,505 - ProgressLogger [INFO] - 1 items processed. Progress is 100%.
hemera      | 2024-06-24 08:18:57,506 - ProgressLogger [INFO] - Finished work. Total items processed: 1. Took 0:00:01.336310.
hemera      | 2024-06-24 08:18:57,529 - exporters.postgres_item_exporter [INFO] - Exporting items to table block_ts_mapper, blocks end, Item count: 2, Took 0:00:00.022562
hemera      | 2024-06-24 08:18:57,530 - ProgressLogger [INFO] - Started work.
```

### Run From Source Code

#### Install Python3 and Pip

Skip this step if you already have both installed.

```bash
sudo apt update
sudo apt install python3
sudo apt install python3-pip
```

#### Initiate Python VENV

Skip this step if you don't want to have a dedicated python venv for Hemera Indexer.

```bash
sudo apt install python3-venv
python3 -m venv ./venv
```

#### Install Pip Dependencies

```bash
source ./venv/bin/activate
sudo apt install libpq-dev
pip install -e .
```

#### Prepare Your PostgreSQL Instance

Hemera Indexer requires a PostgreSQL database to store all indexed data. You may skip this step if you already have a PostgreSQL set up.

##### Setup PostgreSQL

Follow the instructions about how to set up a PostgreSQL database here: [Setup PostgreSQL on Ubuntu](https://www.cherryservers.com/blog/how-to-install-and-setup-postgresql-server-on-ubuntu-20-04).

##### Configure

Configure the `OUTPUT` or `--output` parameter according to your PostgreSQL role information. Check out [Configure Hemera Indexer](#output-or---output) for details.

E.g. `postgresql+psycopg2://${YOUR_USER}:${YOUR_PASSWORD}@${YOUR_HOST}:5432/${YOUR_DATABASE}`.

#### Run

Please check out [Configure Hemera Indexer](#configure-hemera-indexer) on how to configure the indexer.

```bash
python hemera.py stream \
    --provider-uri https://eth.llamarpc.com \
    --debug-provider-uri https://eth.llamarpc.com \
    --postgres-url postgresql+psycopg2://devuser:devpassword@localhost:5432/hemera_indexer \
    --output jsonfile://output/eth_blocks_20000001_20010000/json,csvfile://output/hemera_indexer/csv,postgresql+psycopg2://devuser:devpassword@localhost:5432/eth_blocks_20000001_20010000 \
    --start-block 20000001 \
    --end-block 20010000 \
    # alternatively you can spin up a separate process for traces, as it takes more time
    # --entity-types trace,contract,coin_balance
    --entity-types block,transaction,log,token,token_transfer \
    --block-batch-size 200 \
    --batch-size 200 \
    --max-workers 32
```

Once you have successfully bootstrapped Hemera Indexer, you should be able to view similar logs as below.

```bash
2024-06-25 16:37:38,456 - root [INFO] - Using provider https://eth.llamarpc.com
2024-06-25 16:37:38,456 - root [INFO] - Using debug provider https://eth.llamarpc.com
2024-06-25 16:37:38,485 - alembic.runtime.migration [INFO] - Context impl PostgresqlImpl.
2024-06-25 16:37:38,485 - alembic.runtime.migration [INFO] - Will assume transactional DDL.
2024-06-25 16:37:38,502 - alembic.runtime.migration [INFO] - Context impl PostgresqlImpl.
2024-06-25 16:37:38,502 - alembic.runtime.migration [INFO] - Will assume transactional DDL.
2024-06-25 16:37:39,485 - root [INFO] - Current block 20167548, target block 20137200, last synced block 20137199, blocks to sync 1
2024-06-25 16:37:39,486 - ProgressLogger [INFO] - Started work. Items to process: 1.
2024-06-25 16:37:40,267 - ProgressLogger [INFO] - 1 items processed. Progress is 100%.
2024-06-25 16:37:40,268 - ProgressLogger [INFO] - Finished work. Total items processed: 1. Took 0:00:00.782177.
2024-06-25 16:37:40,283 - exporters.postgres_item_exporter [INFO] - Exporting items to table block_ts_mapper, blocks end, Item count: 2, Took 0:00:00.014799
2024-06-25 16:37:40,283 - ProgressLogger [INFO] - Started work.

```

### Export Result

Hemera Indexer allows you to export the blockchain data to a database, or to JSON/CSV files.

### Export From PostgreSQL Database

#### Connect to Your Postgresql Instance

Use any PostgreSQL client to connect to your PostgreSQL instance, please make sure the `user`, `password`, and `port` is the same as your configuration.

#### Run In Docker

By default, the PostgreSQL port is open on and mapped to port 5432 of your ec2 instance, you can verify or change it in the PostgreSQL section of the `docker-compose.yaml`.

#### Configure Your Network

If you are using any cloud services, make sure the PostgreSQL port is accessible by updating the network rules.

If you are using AWS and EC2, you can check out [this post](https://www.intelligentdiscovery.io/controls/ec2/aws-ec2-postgresql-open) on how to configure the security group.

### Export To Output Files

#### Run In Docker

By default, the `docker-compose.yaml` mounts the `output` folder to `docker-compose/output`, assuming that you are running from `docker-compose` folder.
You can find exported results in `docker-compose/output`.

#### Run From Source Code

The database and exported file locations are the same as what you configured in `OUTPUT` or `--output` parameter.

E.g., If you specify the `OUTPUT` or `--output` parameter as below

```bash
# Command line parameter
python hemera.py stream \
    --provider-uri https://eth.llamarpc.com \
    --debug-provider-uri https://eth.llamarpc.com \
    --postgres-url postgresql+psycopg2://devuser:devpassword@localhost:5432/hemera_indexer \
    --output jsonfile://output/eth_blocks_20000001_20010000/json,csvfile://output/hemera_indexer/csv,postgresql+psycopg2://devuser:devpassword@localhost:5432/eth_blocks_20000001_20010000 \
    --start-block 20000001 \
    --end-block 20010000 \
    --entity-types block,transaction,log,token,token_transfer \
    --block-batch-size 200 \
    --batch-size 200 \
    --max-workers 32

# Or using environment variable
export OUTPUT = postgresql+psycopg2://user:password@localhost:5432/hemera_indexer,jsonfile://output/json, csvfile://output/csv
```

You will be able to find those results in the `output` folder of your current location.

## Configure Hemera Indexer

Hemera indexer can read configuration from cmd line arguments or environment variables.

- If you run Hemera Indexer in [Docker](#run-in-docker), then the environment variable is easier to configure.
- If you prefer running from [Source Code](#run-from-source-code), command line arguments are more intuitive.

Run with `python hemera.py stream --help` to get the latest instructions for arguments.

### Parameters

- If the name of the parameter is in `UPPER_CASE` then it's an environment variable.
- If the name of the parameter starts with `--` then it's a command line argument.

Avoid specifying the same parameter from both the environment variable and the command line argument.

#### `PROVIDER_URI` or `--provider-uri`

[**Default**: `https://mainnet.infura.io`]
The URI of the web3 rpc provider, e.g. `file://$HOME/Library/Ethereum/geth.ipc` or `https://mainnet.infura.io`.

#### `DEBUG_PROVIDER_URI` or `--debug-provider-uri`

[**Default**: `https://mainnet.infura.io`]
The URI of the web3 debug rpc provider, e.g. `file://$HOME/Library/Ethereum/geth.ipc` or `https://mainnet.infura.io`.

#### `POSTGRES_URL` or `--postgres-url`

[**Required**]
The PostgreSQL connection URL that the Hemera Indexer used to maintain its state. e.g. `postgresql+psycopg2://user:password@127.0.0.1:5432/postgres`.

#### `OUTPUT` or `--output`

[**Required**]
You may specify the output parameter so Hemera Indexer will export the data to CSV or JSON files. If not specified the data will be printed to the console.

If you have multiple outputs, use "," to concat the files.
The file location will be relative to your current location if you run from source code, or the `output` folder as configured in `docker-compose.yaml`.

e.g.

- `postgresql+psycopg2://user:password@localhost:5432/hemera_indexer`: Output will be exported to your postgres.
- `jsonfile://output/json`: Json files will be exported to folder `output/json`
- `csvfile://output/csv`: Csv files will be exported to folder `output/csv`
- `console,jsonfile://output/json,csvfile://output/csv`: Multiple destinations are supported.

#### `ENTITY_TYPES` or `--entity-types`

[**Default**: `BLOCK,TRANSACTION,LOG,TOKEN,TOKEN_TRANSFER`]
Hemera Indexer will export those entity types to your database and files(if `OUTPUT` is specified).
Full list of available entity types:

- `block`
- `transaction`
- `log`
- `token`
- `token_transfer`
- `trace`
- `contract`
- `coin_balance`
- `token_balance`
- `token_ids`

If you didn't specify this parameter, the default entity types will be BLOCK,TRANSACTION,LOG,TOKEN,TOKEN_TRANSFER.

You may spawn up multiple Hemera Indexer processes, each of them indexing different entity types to accelerate the indexing process. For example, indexing `trace` data may take much longer than other entities, you may want to run a separate process to index `trace` data. Checkout `docker-compose/docker-compose.yaml` for examples.

#### `DB_VERSION` or `--db-version`

[**Default**: `head`]
The database version to initialize the database. Using the Alembic script's revision ID to specify a version.
e.g. `head`, indicates the latest version.
Or `base`, indicates the empty database without any table.
Default value: `head`

#### `START_BLOCK` or `--start-block`

The block number to start from, e.g. `0`, `1000`, etc.
If you don't specify this, Hemera Indexer will read the last synced block from the PostgreSQL database and resume from it.

#### `END_BLOCK` or `--end-block`

The block number that ends at, e.g. `10000`, `20000`, etc.

#### `PARTITION_SIZE` or `--partition-size`

[**Default**: `50000`]
The number of records to write to each file.

#### `PERIOD_SECONDS` or `--period-seconds`

[**Default**: `10`]
Seconds to sleep between each sync with the latest blockchain state.

#### `BATCH_SIZE` or `--batch-size`

[**Default**: `10`]
The number of non-debug rpc requests to batch in a single request.

#### `DEBUG_BATCH_SIZE` or `--debug-batch-size`

[**Default**: `1`]
The number of debug rpc to batch in a single request.

#### `BLOCK_BATCH_SIZE` or `--block-batch-size`

[**Default**: `1`]
The number of blocks to batch in a single sync round.

#### `MAX_WORKERS` or `--max-workers`

[**Default**: `5`]
The number of workers, e.g. `4`, `5`, etc.

#### `LOG_FILE` or `--log-file`

The log file to use. e.g. `path/to/logfile.log`.
