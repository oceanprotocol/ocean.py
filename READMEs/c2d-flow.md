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
export TEST_PRIVATE_KEY1=0x5d75837394b078ce97bc289fa8d75e21000573520bfa7784a9d28ccaae602bf8
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209

#needed to mint fake OCEAN for testing with ganache
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

#Mint OCEAN for ganache only
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
```

## 2. Alice publishes data asset

In the same Python console:
```python
#Publish DATA datatoken, mint tokens
from ocean_lib.web3_internal.currency import to_wei

DATA_datatoken = ocean.create_data_token('DATA1', 'DATA1', alice_wallet, blob=ocean.config.metadata_cache_uri)
DATA_datatoken.mint(alice_wallet.address, to_wei(100), alice_wallet)
print(f"DATA_datatoken.address = '{DATA_datatoken.address}'")

#Specify metadata & service attributes for Branin test dataset.
# It's specified using _local_ DDO metadata format; Aquarius will convert it to remote
# by removing `url` and adding `encryptedFiles` field.
DATA_date_created = "2019-12-28T10:55:11Z"
DATA_metadata = {
    "main": {
        "type": "dataset",
        "files": [
	  {
	    "url": "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff",
	    "index": 0,
	    "contentType": "text/text"
	  }
	],
	"name": "branin", "author": "Trent", "license": "CC0",
	"dateCreated": DATA_date_created
    }
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

#Set up a service provider. We'll use this same provider for ALG
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
service_endpoint = DataServiceProvider.get_url(ocean.config)
#returns "http://localhost:8030"

#Calc DATA service tuple
from ocean_lib.common.agreements.service_factory import ServiceDescriptor
DATA_service_tuple = ServiceDescriptor.compute_service_descriptor(DATA_service_attributes, service_endpoint)
# DATA_service_tuple = ServiceDescriptor.access_service_descriptor(DATA_service_attributes, service_endpoint)
#returns ("compute",
#         {"attributes": DATA_service_attributes, "serviceEndpoint": service_endpoint})

#Publish metadata and service info on-chain
DATA_ddo = ocean.assets.create(
  metadata=DATA_metadata, # {"main" : {"type" : "dataset", ..}, ..}
  publisher_wallet=alice_wallet,
  service_descriptors=[DATA_service_tuple], # [("compute", {"attributes": ..})]
  data_token_address=DATA_datatoken.address)
print(f"DATA did = '{DATA_ddo.did}'")
```

Full details: [DATA_ddo](DATA_ddo.md)


## 3. Alice publishes algorithm

In the same Python console:
```python
#Publish ALG datatoken
ALG_datatoken = ocean.create_data_token('ALG1', 'ALG1', alice_wallet, blob=ocean.config.metadata_cache_uri)
ALG_datatoken.mint(alice_wallet.address, to_wei(100), alice_wallet)
print(f"ALG_datatoken.address = '{ALG_datatoken.address}'")

#Specify metadata and service attributes, for "GPR" algorithm script.
# In same location as Branin test dataset. GPR = Gaussian Process Regression.
ALG_date_created = "2020-01-28T10:55:11Z"
ALG_metadata =  {
    "main": {
        "type": "algorithm",
        "algorithm": {
            "language": "python",
            "format": "docker-image",
            "version": "0.1",
            "container": {
              "entrypoint": "node $ALGO",
              "image": "node",
              "tag": "10"
            }
        },
        "files": [
	  {
	    "url": "https://raw.githubusercontent.com/trentmc/branin/main/gpr.py",
	    "index": 0,
	    "contentType": "text/text",
	  }
	],
	"name": "gpr", "author": "Trent", "license": "CC0",
	"dateCreated": ALG_date_created
    }
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

#Calc ALG service tuple. We use the same service provider as DATA
ALG_service_tuple = ServiceDescriptor.access_service_descriptor(ALG_service_attributes, service_endpoint)
#returns ("algorithm",
#         {"attributes": ALG_service_attributes, "serviceEndpoint": service_endpoint})

#Publish metadata and service info on-chain
ALG_ddo = ocean.assets.create(
  metadata=ALG_metadata, # {"main" : {"type" : "algorithm", ..}, ..}
  publisher_wallet=alice_wallet,
  service_descriptors=[ALG_service_tuple], 
  data_token_address=ALG_datatoken.address)
print(f"ALG did = '{ALG_ddo.did}'")
```

Full details: [ALG_ddo](ALG_ddo.md)

## 4. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
from ocean_lib.assets import utils
utils.add_publisher_trusted_algorithm(DATA_ddo.did, ALG_ddo.did, config.metadata_cache_uri)
```

## 5. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
bob_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY2'))
print(f"bob_wallet.address = '{bob_wallet.address}'")
 
#Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.web3, ocean.OCEAN_address)
assert OCEAN_token.balanceOf(alice_wallet.address) > 0, "need OCEAN"
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

#alice shares access for both to bob, as datatokens. Alternatively, bob might have bought these in a market.
DATA_datatoken.transfer(bob_wallet.address, to_wei(5), from_wallet=alice_wallet)
ALG_datatoken.transfer(bob_wallet.address, to_wei(5), from_wallet=alice_wallet)
```

## 6. Bob starts a compute job

Only inputs needed: DATA_did, ALG_did. Everything else can get computed as needed.


What's below is based on the end-to-end example in ocean.js-cli/src/commands.ts::compute() (starts line 205 in commands.ts). WIP!


In the same Python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
DATA_did = DATA_ddo.did
ALG_did = ALG_ddo.did
DATA_DDO = ocean.assets.resolve(DATA_did)
ALG_DDO = ocean.assets.resolve(ALG_did)

compute_service = DATA_DDO.get_service('compute')
algo_service = ALG_DDO.get_service('access')

from ocean_lib.web3_internal.constants import ZERO_ADDRESS

#order & pay for dataset
order_requirements_dataset = ocean.assets.order(DATA_did, bob_wallet.address, service_type=compute_service.type)
DATA_order_tx_id = ocean.assets.pay_for_service(
        ocean.web3,
        order_requirements_dataset.amount,
        order_requirements_dataset.data_token_address,
        DATA_did,
        compute_service.index,
        ZERO_ADDRESS,
        bob_wallet,
        order_requirements_dataset.computeAddress,
    )

#order & pay for algo
order_requirements_algorithm = ocean.assets.order(ALG_did, bob_wallet.address, service_type=algo_service.type)
ALG_order_tx_id = ocean.assets.pay_for_service(
        ocean.web3,
        order_requirements_algorithm.amount,
        order_requirements_algorithm.data_token_address,
        ALG_did,
        algo_service.index,
        ZERO_ADDRESS,
        bob_wallet,
        order_requirements_algorithm.computeAddress,
)
#Interface at https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/data_provider/data_service_provider.py

signature = ocean.compute._sign_message(
            bob_wallet, 
            f"{bob_wallet.address}{DATA_did}",
            service_endpoint=service_endpoint
)

response = DataServiceProvider.start_compute_job(
    did=DATA_did,
    service_endpoint=service_endpoint,
    consumer_address=bob_wallet.address,
    signature=signature,
    service_id=compute_service.index,
    order_tx_id=DATA_order_tx_id,
    algorithm_did=ALG_did,
    algorithm_tx_id=ALG_order_tx_id,
    algorithm_data_token=ALG_datatoken.address,
)
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
