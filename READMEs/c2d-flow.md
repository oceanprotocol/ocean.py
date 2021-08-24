<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Compute-to-Data (C2D) Flow

This quickstart describes a C2D fow.

Here are the steps:

1. Setup
2. Alice publishes data asset
3. Alice publishes algorithm
4. Alice allows the algorithm for C2D for that data asset
5. Bob acquires datatokens for data and algorithm
6. Bob starts a compute job
7. Bob monitors logs / algorithm output 

Let's go through each step.

## 1. Setup

### Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

### Run barge services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

#run barge: start ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh  --with-provider2
```

### Install the library

In a new console that we'll call the work console (as we'll use it later):

```console
#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library. Install wheel first to avoid errors.
pip install wheel
pip install ocean-lib
```

### Create config file

In the work console:
```console
#Create config.ini file and fill it with configuration info
echo """
[eth-network]
network = http://127.0.0.1:8545
address.file = ~/.ocean/ocean-contracts/artifacts/address.json

[resources]
metadata_cache_uri = http://localhost:5000
provider.url = http://localhost:8030
provider.address = 0x00bd138abd70e2f00903268f3db08f2d25677c9e

downloads.path = consume-downloads
""" > config.ini
```

### Set envvars

In the work console:
```console
#set private keys of two accounts
export TEST_PRIVATE_KEY1=0xbbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d
export TEST_PRIVATE_KEY2=0x804365e293b9fab9bd11bddd39082396d56d30779efbb3ffb0a6089027902c4a

#needed to mint fake OCEAN
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

### Config in Python

In the work console:
```console
python
```

For the following steps, we use the Python console. Keep it open between steps.

In the Python console:
```python
#create ocean instance
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
config = Config('config.ini')
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

#Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY1'))
print(f"alice_wallet.address = '{alice_wallet.address}'")
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

#Set up a service provider. For simplicity, use the same provider for DATA and ALG
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.common.agreements.service_factory import ServiceDescriptor
service_endpoint = DataServiceProvider.get_url(ocean.config)
```

## 2. Alice publishes data asset

In the same Python console:
```python
#Publish DATA datatoken, mint tokens
DATA_datatoken = ocean.create_data_token('DATA1', 'DATA1', alice_wallet, blob=ocean.config.metadata_cache_uri)
DATA_datatoken.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
print(f"DATA_datatoken.address = '{DATA_datatoken.address}'")

#Specify metadata and service attributes, using the Branin test dataset
DATA_date_created = "2019-12-28T10:55:11Z"
DATA_metadata =  {
    "main": {
        "type": "dataset", "name": "branin", "author": "Trent",
        "license": "CC0: Public Domain", "dateCreated": DATA_date_created,
        "files": [{"index": 0, "contentType": "text/text",
	           "url": "https://raw.githubusercontent.com/trentmc/branin/master/branin.arff"}]}
}
DATA_service_attributes = {
        "main": {
            "name": "DATA_dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "timeout": 3600 * 24,
            "datePublished": DATA_date_created,
            "cost": 1.0, # <don't change, this is obsolete>
        }
    }

#Publish metadata and service info on-chain
DATA_service = ServiceDescriptor.access_service_descriptor(DATA_service_attributes, service_endpoint)
DATA_asset = ocean.assets.create(
  DATA_metadata,
  alice_wallet,
  service_descriptors=[DATA_service],
  data_token_address=DATA_datatoken.address)
print(f"DATA_asset.did = '{DATA_asset.did}'")

```

## 3. Alice publishes algorithm

In the same Python console:
```python
#Publish ALG datatoken
ALG_datatoken = ocean.create_data_token('ALG1', 'ALG1', alice_wallet, blob=ocean.config.metadata_cache_uri)
ALG_datatoken.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
print(f"ALG_datatoken.address = '{ALG_datatoken.address}'")

#Specify metadata and service attributes, using the Branin test dataset
ALG_date_created = "2020-01-28T10:55:11Z"
ALG_metadata =  {
    "main": {
        "type": "algorithm", "name": "gpr", "author": "Trent",
        "license": "CC0: Public Domain", "dateCreated": ALG_date_created,
        "files": [{"name" : "build_model", 
	           "url": "https://raw.githubusercontent.com/trentmc/branin/master/gpr.py",
		   "index": 0, "contentType": "text/plain",
		   }]}
}
ALG_service_attributes = {
        "main": {
            "name": "ALG_dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "timeout": 3600 * 24,
            "datePublished": ALG_date_created,
            "cost": 1.0, # <don't change, this is obsolete>
        }
    }

#Publish metadata and service info on-chain
ALG_service = ServiceDescriptor.access_service_descriptor(ALG_service_attributes, service_endpoint)
ALG_asset = ocean.assets.create(
  ALG_metadata,
  alice_wallet,
  service_descriptors=[ALG_service],
  data_token_address=ALG_datatoken.address)
print(f"ALG_asset.did = '{ALG_asset.did}'")
```

## 4. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
from ocean_lib.assets import utils
utils.add_publisher_trusted_algorithm(DATA_did, ALG_did, config.metadata_cache_uri)
```

## 5. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
#alice shares access for both to bob, as datatokens. Alternatively, bob might have bought these in a market.
DATA_datatoken.transfer(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
ALG_datatoken.transfer(bob_address, to_base_18(1.0), from_wallet=alice_wallet)
```

## 6. Bob starts a compute job

Only inputs needed: DATA_did, ALG_did. Everything else can get computed as needed.


What's below is based on the end-to-end example in ocean.js-cli/src/commands.ts::compute() (starts line 205 in commands.ts). WIP!


In the same Python console:
```python
DATA_DDO = resolve(DATA_did)
ALG_DDO = resolved(ALG_did)

compute_service = ocean_lib.assets.getServiceByType(DATA_did, 'compute')
algo_service = ocean_lib.assets.getServiceByType(DATA_did, 'access')

compute_address = ocean_lib.compute.getComputeAddress(DATA_did, compute_service.index)
algo_definition = ComputeAlgorithm(did=ALG_did, serviceIndex=algo_service.index)

DATA_order_tx = ocean_lib.compute.orderAsset(DATA_did, .compute_service.index, algo_definition, from_wallet=bob_wallet)
ALG_order_tx = ocean_lib.compute.orderAlgorithm(ALG_did, algo_service.type, algo_service.index, from_wallet=bob_wallet)

#Interface at https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/data_provider/data_service_provider.py
response = DataServiceProvider.start_compute_job(
  did=DATA_did,
  service_endpoint=service_endpoint,
  consumer_address=ALG_datatoken.address,
  signature=FIXME,
  order_tx_id=ALG_order_tx.id,
  algorithm_did=ALG_did)
print(f"Started compute job. Info: {response}")
print(f"  JobID: FIXME")
```

## 7. Bob monitors logs / algorithm output 

What's below is based on the end-to-end example in ocean.js-cli/src/commands.ts::getCompute() (starts line 285 in commands.ts). WIP!
- In turn, it uses ocean.js/src/ocean/Compute.ts (starts line 201):
```
Args:
   * @param  {Account} consumerAccount The account of the consumer ordering the service.
   * @param  {string} did Decentralized identifier.
   * @param  {string} jobId The jobId of the compute job
   * @param  {string} jobId The Order transaction id
   * @param  {boolean} sign If the provider request is going to be signed(default) (full status) or not (short status)
```


In the same Python console:
```python
FIXME
```
