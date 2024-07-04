<!-- TOC -->
* [Introduction](#introduction)
* [Prerequisites](#prerequisites)
  * [Disk Size](#disk-size)
    * [Entity Types](#entity-types)
  * [VM](#vm)
    * [Crete VM From Cloud Services](#crete-vm-from-cloud-services)
* [Install and Run Hemera Indexer](#install-and-run-hemera-indexer)
  * [Clone the Repository](#clone-the-repository)
  * [Run Hemera Indexer](#run-hemera-indexer)
    * [Run In Docker](#run-in-docker)
      * [Install Docker & Docker Compose](#install-docker--docker-compose)
      * [Enter the Docker Compose Folder](#enter-the-docker-compose-folder)
    * [Run From Source Code](#run-from-source-code)
      * [Install Python3 and Pip](#install-python3-and-pip)
      * [Initiate Python VENV](#initiate-python-venv)
      * [Install Pip Dependencies](#install-pip-dependencies)
      * [Prepare Your PostgresQL Instance](#prepare-your-postgresql-instance)
        * [Setup PostgresQL](#setup-postgresql)
        * [Configure](#configure)
      * [Run](#run)
* [Configure Hemera Indexer](#configure-hemera-indexer)
  * [Parameters](#parameters)
      * [`PROVIDER_URI` or `--provider-uri`](#provider_uri-or---provider-uri)
      * [`DEBUG_PROVIDER_URI` or `--debug-provider-uri`](#debug_provider_uri-or---debug-provider-uri)
      * [`POSTGRES_URL` or `--postgres-url`](#postgres_url-or---postgres-url)
      * [`OUTPUT` or `--output`](#output-or---output)
      * [`ENTITY_TYPES` or `--entity-types`](#entity_types-or---entity-types)
      * [`DB_VERSION` or `--db-version`](#db_version-or---db-version)
      * [`START_BLOCK` or `--start-block`](#start_block-or---start-block)
      * [`END_BLOCK` or `--end-block`](#end_block-or---end-block)
      * [`PARTITION_SIZE` or `--partition-size`](#partition_size-or---partition-size)
      * [`PERIOD_SECONDS` or `--period-seconds`](#period_seconds-or---period-seconds)
      * [`BATCH_SIZE` or `--batch-size`](#batch_size-or---batch-size)
      * [`DEBUG_BATCH_SIZE` or `--debug-batch-size`](#debug_batch_size-or---debug-batch-size)
      * [`BLOCK_BATCH_SIZE` or `--block-batch-size`](#block_batch_size-or---block-batch-size)
      * [`MAX_WORKERS` or `--max-workers`](#max_workers-or---max-workers)
      * [`LOG_FILE` or `--log-file`](#log_file-or---log-file)
* [Export Result](#export-result)
  * [Export From Postgresql Database](#export-from-postgresql-database)
    * [Connect to Your Postgresql Instance](#connect-to-your-postgresql-instance)
      * [Run In Docker](#run-in-docker-1)
      * [Update AWS Security Groups](#update-aws-security-groups)
  * [Export From Output Files](#export-from-output-files)
      * [Run In Docker](#run-in-docker-2)
      * [Run From Source Code](#run-from-source-code-1)
<!-- TOC -->

# Introduction

Hemera Indexer reads information from a blockchain and extracts specific data such as blocks, transactions, and specific
types of transactions to a postgres database or CSV/JSON files.

# Prerequisites

- VM
  - Ubuntu
    - Technically, you can run hemera indexer on any python compatible platform but for simplicity, this documentation is based on Ubuntu.
- RPC Node of your EVM compatible blockchain


## Disk Size

### Entity Types
Based on the 2024 Ethereum, every 25k blocks, which is approximate 4.5 million transactions, consume disk size as below
- 9GB PostgresQL database
- 9.3GB CSV file, if you opt for the csv export.
- 15GB Json file, if you opt for the json export
  That is about 35GB for every 25k blocks, for every 100k blocks, we recommend at least 150 GB for every 100k eth blocks.


## VM

### Crete VM From Cloud Services

If you don't have a VM in place, you can create VMs from cloud providers.
[Create an AWS EC2 Instance](docs/AWS.md)

# Install and Run Hemera Indexer

## Clone the Repository

```bash
git clone git@github.com:socialscan-io/hemera_indexer.git
```

## Run Hemera Indexer
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

#### Enter the Docker Compose Folder

```bash
cd hemera_indexer
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
You should be able to see similar logs from your console that indicates hemera indexer is running properly.
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
Skip this step if you don't want to have a dedicated python venv for hemera indexer.
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


#### Prepare Your PostgresQL Instance
Hemera indexer requires a postgresql database to record all the data. You may skip this step if you already have a postgresql database set up.

##### Setup PostgresQL
Follow the instructions about how to set up a postgresql database here: [Setup PostgresQL on Ubuntu](https://www.cherryservers.com/blog/how-to-install-and-setup-postgresql-server-on-ubuntu-20-04).

##### Configure
Configure the `OUTPUT` or `--output` parameter according to your postgresql role information. Checkout [Configure Hemera Indexer](#output-or---output) for details.

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
    --entity-types block,transaction,log,token,token_transfer \
    --block-batch-size 200 \
    --batch-size 200 \
    --max-workers 32
```

Once you have successfully bootstrapped hemera indexer, you should be able to view similar logs as below.
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


# Configure Hemera Indexer
Hemera indexer can read configuration from cmd line arguments or environment variables.

- If you run Hemera Indexer in [Docker](#run-in-docker), then environment variable is easier to config.
- If you prefer running from [Source Code](#run-from-source-code), cmd lien arguments is more intuitive.
  - Run with `python stream.py --help` to get the latest instructions of arguments.

## Parameters
- If the name of the parameter is in `UPPER_CASE` then it's environment variable.
- If the name of the parameter starts with `--` then it's a cmd line argument.

Avoid specifying the same parameter from both environment variable and cmd line.
#### `PROVIDER_URI` or `--provider-uri`
[**Default**: `https://mainnet.infura.io`]
The URI of the web3 provider, e.g. `file://$HOME/Library/Ethereum/geth.ipc` or `https://mainnet.infura.io`.

---

#### `DEBUG_PROVIDER_URI` or `--debug-provider-uri`
[**Default**: `https://mainnet.infura.io`]
The URI of the web3 debug provider, e.g. `file://$HOME/Library/Ethereum/geth.ipc` or `https://mainnet.infura.io`.

---

#### `POSTGRES_URL` or `--postgres-url`
[**Required**]
The postgresql connection url that hemera used to maintain its state. e.g. `postgresql+psycopg2://user:password@127.0.0.1:5432/postgres`.

---

#### `OUTPUT` or `--output`
[**Required**]
You may specify the output parameter so hemera will export the data to csv or json files as well. If not specified the data will be printed to the console.

If you have multi outputs, use "," to concat the files.
The file location will be relative to your current location if you run from source code, or the `output` folder as configured in `docker-compose.yaml`.

e.g.
- `postgresql+psycopg2://user:password@localhost:5432/hemera_indexer`: Output will be exported to your postgres.
- `jsonfile://output/json`: Json files will be exported to folder `output/json`
- `csvfile://output/csv`: Csv files will be exported to folder `output/csv`
- `console,jsonfile://output/json,csvfile://output/csv`: Multiple destinations are supported.

---

#### `ENTITY_TYPES` or `--entity-types`
[**Default**: `<value of ALL_ENTITY_COLLECTIONS>`]
Hemera indexer will export those entity types to your database and files(if `OUTPUT` is specified).
Full list of available entity types:
- `block`
- `transaction`
- `log`
- `token`
- `token_transfer`
- `trace`
- `contract`
- `coin_balance`

If you didn't specify this parameter, the default entity types will be all of the above.

You may spawn up multi hemera indexer processes, each of them is indexing different entity types to accelrate the syncing process, as traces may take much longer than other entities, checkout 'docker-compose/docker-compose.yaml' for examples.

---

#### `DB_VERSION` or `--db-version`
[**Default**: `head`]
The database version to initialize the database. Using the Alembic script's revision ID to specify a version.  
e.g. `head`, indicates the latest version.  
Or `base`, indicates the empty database without any table.  
Default value: `head`
---

#### `START_BLOCK` or `--start-block`
The block number to start from, e.g. `0`, `1000`, etc.

If you don't specify this, hemera will read the last synced block from the postgresql database and resume from it.

---

#### `END_BLOCK` or `--end-block`
The block number that ends at, e.g. `10000`, `20000`, etc.

---

#### `PARTITION_SIZE` or `--partition-size`
[**Default**: `50000`]
How many records to write to each file.

---

#### `PERIOD_SECONDS` or `--period-seconds`
[**Default**: `10`]
How many seconds to sleep between syncs.

---

#### `BATCH_SIZE` or `--batch-size`
[**Default**: `10`]
How many parameters to batch in a single request.

---

#### `DEBUG_BATCH_SIZE` or `--debug-batch-size`
[**Default**: `1`]
How many parameters to batch in a single debug RPC request.

---

#### `BLOCK_BATCH_SIZE` or `--block-batch-size`
[**Default**: `1`]
How many blocks to batch in a single sync round.

---

#### `MAX_WORKERS` or `--max-workers`
[**Default**: `5`]
The number of workers, e.g. `4`, `5`, etc.

---

#### `LOG_FILE` or `--log-file`
The log file to use. e.g. `path/to/logfile.log`.

# Export Result
Hemera indexer allows you to export the blockchain data to a database, or to json/csv files.
## Export From Postgresql Database
### Connect to Your Postgresql Instance
Use you any PostgresQL client to connect to your postgresql instance, please make sure the `user`, `password` and `port` is the same as your configuration.
#### Run In Docker
By default, the postgresql port is open on and mapped to port 5432 of your ec2 instance, you can verify or change it in the postgresql section of the `docker-compose.yaml`.
#### Update AWS Security Groups
If you are using AWS ec2, make sure the postgresql port is accessible by updating the security groups of your ec2 instance.

You can check out [this post](https://www.intelligentdiscovery.io/controls/ec2/aws-ec2-postgresql-open) on how to configure the security group.


## Export From Output Files
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

