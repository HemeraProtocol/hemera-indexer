# Operator Guide

## Key generation and wallet funding
Follow [EigenLayer](https://docs.eigenlayer.xyz/docs/getting-started/installation) and Install EigenLayer CLI

Generate ECDSA and BLS keypair using the following command

```
eigenlayer operator keys create --key-type ecdsa [keyname]
eigenlayer operator keys create --key-type bls [keyname]
```

**💡 Please ensure you backup your private keys to a safe location. By default, the encrypted keys will be stored in ~/.eigenlayer/operator_keys/**


## Register on EigenLayer as an operator

**💡 You may skip the following steps if you are already a registered operator on the EigenLayer testnet and mainnet.**

**You will need to do it once for testnet and once for mainnet.**


1. Create the configuration files needed for operator registration using the following commands. Follow the step-by-step prompt. Once completed, operator.yaml and metadata.json will be created.

```
eigenlayer operator config create
```

2. Edit `metadata.json` and fill in your operator's details.

```
{
  "name": "Example Operator",
  "website": "<https://example.com/>",
  "description": "Example description",
  "logo": "<https://example.com/logo.png>",
  "twitter": "<https://twitter.com/example>"
}
```

3. Upload `metadata.json` to a public URL. Then update the `operator.yaml` file with the url (`metadata_url`). If you need hosting service to host the metadata, you can consider uploading the metadata [gist](https://gist.github.com/) and get the `raw` url.

4. If this is your first time registering this operator, run the following command to register and update your operator

```
eigenlayer operator register operator.yaml
```

Upon successful registration, you should see

```
✅ Operator is registered successfully to EigenLayer
```

If you need to edit the metadata in the future, simply update metadata.json and run the following command

```
eigenlayer operator update operator.yaml
```

5. After your operator has been registered, it will be reflected on the EigenLayer operator page.

Testnet: https://holesky.eigenlayer.xyz/operator

Mainnet: https://app.eigenlayer.xyz/operator

You can also check the operator registration status using the following command.

```
eigenlayer operator status operator.yaml
```

## Joining Hemera AVS
Contact us to add the operator address to the whitelist.

### Register Operators
Follow [alt-research](https://github.com/alt-research/mach-avs/blob/m2-dev/scripts/README.md) and register the operator using `register_operator.sh`

### Configuration

Edit the configuration file `indexer-config-avs-holesky.yaml` in the config directory, the configuration item that must be updated is `operator_ecdsa_key_file` and `operator_bls_key_file`.

### RUN

** Run by source code **

```
cd hemera_indexer
python3 hemera.py stream --provider-uri https://holesky.drpc.org --debug-provider-uri https://holesky.drpc.org -O hemera_history_transparency --output postgres --postgres-url
postgresql://postgres:123456@localhost:5432/hemera_indexer --config-file ./config/indexer-config-avs-holesky.yaml
```

** Run by docker **
```commandline
cd hemera_indexer
cd docker-compose
vim avs.env
sudo docker compose -f avs-operator.yaml up
```








