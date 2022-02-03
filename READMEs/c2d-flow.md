<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Compute-to-Data (C2D) Flow

This quickstart describes a C2D flow.

Here are the steps:

1. Setup
2. Alice publishes data asset
3. Alice publishes algorithm
4. Alice allows the algorithm for C2D for that data asset
5. Bob acquires datatokens for data and algorithm
6. Bob starts a compute job
7. Bob monitors logs / algorithm output

This c2d flow example features a simple algorithm from the field of ML. Ocean c2d is not limited to ML datasets and algorithms, but it is one of the most common use cases. Besides the flow below, two other worked C2D flows are: (a) simple image processing at [ocean-lena](https://github.com/calina-c/ocean-lena/blob/main/c2d-flow.md), (b) logistic regression for classification [blog post](https://medium.com/ravenprotocol/machine-learning-series-using-logistic-regression-for-classification-in-oceans-compute-to-data-18df49b6b165) with both GUI and CLI flows.

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Install extra libraries

This example uses c2d to create a regression model. In order to visualise it or manipulate it, you also need some dependencies.

In your project folder, in this case my_project from `Setup : Install the library` in First Steps, run the following command:

```console
pip install numpy matplotlib
```

### Set envvars

In the work console:
```console
#set private keys of two accounts
export TEST_PRIVATE_KEY1=0x5d75837394b078ce97bc289fa8d75e21000573520bfa7784a9d28ccaae602bf8
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209

#set the address file only for ganache
export ADDRESS_FILE=~/.ocean/ocean-contracts/artifacts/address.json

#set network URL
export OCEAN_NETWORK_URL=http://127.0.0.1:8545
```

### Start Python

In the work console:
```console
python
```

For the following steps, we use the Python console. Keep it open between steps.

In the Python console:
```python
#create ocean instance
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_wallet = Wallet(
    ocean.web3,
    os.getenv('TEST_PRIVATE_KEY1'),
    config.block_confirmations,
    config.transaction_timeout,
)
print(f"alice_wallet.address = '{alice_wallet.address}'")
```

## 2. Alice publishes data asset

In the same Python console:
```python
# Publish DATA datatoken, mint tokens
from ocean_lib.web3_internal.currency import to_wei

DATA_datatoken = ocean.create_datatoken('DATA1', 'DATA1', alice_wallet, blob=ocean.config.metadata_cache_uri)
DATA_datatoken.mint(alice_wallet.address, to_wei(100), alice_wallet)
print(f"DATA_datatoken.address = '{DATA_datatoken.address}'")

# Specify metadata & service attributes for Branin test dataset.
# It's specified using _local_ DDO metadata format; Aquarius will convert it to remote
# by removing `url` and adding `encryptedFiles` field.
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
	"dateCreated": "2019-12-28T10:55:11Z"
    }
}
DATA_service_attributes = {
    "main": {
        "name": "DATA_dataAssetAccessServiceAgreement",
        "creator": alice_wallet.address,
        "timeout": 3600 * 24,
        "datePublished": "2019-12-28T10:55:11Z",
        "cost": 1.0, # <don't change, this is obsolete>
        }
    }

# Set up a service provider. We'll use this same provider for ALG
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
provider_url = DataServiceProvider.get_url(ocean.config)
# returns "http://localhost:8030"

# Calc DATA service compute descriptor
from ocean_lib.services.service import Service
from ocean_lib.agreements.service_types import ServiceTypes
DATA_compute_service = Service(
    service_endpoint=provider_url,
    service_type=ServiceTypes.CLOUD_COMPUTE,
    attributes=DATA_service_attributes
)

#Publish metadata and service info on-chain
DATA_ddo = ocean.assets.create(
  metadata=DATA_metadata, # {"main" : {"type" : "dataset", ..}, ..}
  publisher_wallet=alice_wallet,
  services=[DATA_compute_service],
  datatoken_address=DATA_datatoken.address)
print(f"DATA did = '{DATA_ddo.did}'")
```

Full details: [DATA_ddo](DATA_ddo.md)


## 3. Alice publishes algorithm

For this step, there are some prerequisites needed. If you want to replace the sample algorithm with an algorithm of your choosing, you will need to do some dependency management.
You can use one of the standard [Ocean algo_dockers images](https://github.com/oceanprotocol/algo_dockers) or publish a custom docker image.
Use the image name and tag in the `container` part of the algorithm metadata.
This docker image needs to have basic support for dependency installation e.g. in the case of Python, OS-level library installations, pip installations etc.
Take a look at the [Ocean tutorials](https://docs.oceanprotocol.com/tutorials/compute-to-data-algorithms/) to learn more about docker image publishing.

In the same Python console:
```python
# Publish ALG datatoken
ALG_datatoken = ocean.create_datatoken('ALG1', 'ALG1', alice_wallet, blob=ocean.config.metadata_cache_uri)
ALG_datatoken.mint(alice_wallet.address, to_wei(100), alice_wallet)
print(f"ALG_datatoken.address = '{ALG_datatoken.address}'")

# Specify metadata and service attributes, for "GPR" algorithm script.
# In same location as Branin test dataset. GPR = Gaussian Process Regression.
ALG_metadata =  {
    "main": {
        "type": "algorithm",
        "algorithm": {
            "language": "python",
            "format": "docker-image",
            "version": "0.1",
            "container": {
              "entrypoint": "python $ALGO",
              "image": "oceanprotocol/algo_dockers",
              "tag": "python-branin"
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
	"dateCreated": "2020-01-28T10:55:11Z"
    }
}
ALG_service_attributes = {
        "main": {
            "name": "ALG_dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "timeout": 3600 * 24,
            "datePublished": "2020-01-28T10:55:11Z",
            "cost": 1.0, # <don't change, this is obsolete>
        }
    }

# Calc ALG service access descriptor. We use the same service provider as DATA
ALG_access_service = Service(
    service_endpoint=provider_url,
    service_type=ServiceTypes.CLOUD_COMPUTE,
    attributes=ALG_service_attributes
)

# Publish metadata and service info on-chain
ALG_ddo = ocean.assets.create(
  metadata=ALG_metadata, # {"main" : {"type" : "algorithm", ..}, ..}
  publisher_wallet=alice_wallet,
  services=[ALG_access_service],
  datatoken_address=ALG_datatoken.address)
print(f"ALG did = '{ALG_ddo.did}'")
```

Full details: [ALG_ddo](ALG_ddo.md)

Please note that this example features a simple Python algorithm. If you publish an algorithm in another language, make sure you have an appropriate container to run it, including dependencies.
You can find more information about how to do this in the [Ocean tutorials](https://docs.oceanprotocol.com/tutorials/compute-to-data-algorithms/).

## 4. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
from ocean_lib.assets import utils
utils.add_publisher_trusted_algorithm(DATA_ddo, ALG_ddo.did, config.metadata_cache_uri)
ocean.assets.update(DATA_ddo, publisher_wallet=alice_wallet)
```

## 5. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
bob_wallet = Wallet(
    ocean.web3,
    os.getenv('TEST_PRIVATE_KEY2'),
    config.block_confirmations,
    config.transaction_timeout,
)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Alice shares access for both to Bob, as datatokens. Alternatively, Bob might have bought these in a market.
DATA_datatoken.transfer(bob_wallet.address, to_wei(5), from_wallet=alice_wallet)
ALG_datatoken.transfer(bob_wallet.address, to_wei(5), from_wallet=alice_wallet)
```

## 6. Bob starts a compute job

Only inputs needed: DATA_did, ALG_did. Everything else can get computed as needed.

In the same Python console:
```python
DATA_did = DATA_ddo.did  # for convenience
ALG_did = ALG_ddo.did
DATA_DDO = ocean.assets.resolve(DATA_did)  # make sure we operate on the updated and indexed metadata_cache_uri versions
ALG_DDO = ocean.assets.resolve(ALG_did)

compute_service = DATA_DDO.get_service('compute')
algo_service = ALG_DDO.get_service('access')

from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.models.compute_input import ComputeInput

# order & pay for dataset
dataset_order_requirements = ocean.assets.order(
    DATA_did, bob_wallet.address, service_type=compute_service.type
)
DATA_order_tx_id = ocean.assets.pay_for_service(
        ocean.web3,
        dataset_order_requirements.amount,
        dataset_order_requirements.datatoken_address,
        DATA_did,
        compute_service.index,
        ZERO_ADDRESS,
        bob_wallet,
        dataset_order_requirements.computeAddress,
    )

# order & pay for algo
algo_order_requirements = ocean.assets.order(
    ALG_did, bob_wallet.address, service_type=algo_service.type
)
ALG_order_tx_id = ocean.assets.pay_for_service(
        ocean.web3,
        algo_order_requirements.amount,
        algo_order_requirements.datatoken_address,
        ALG_did,
        algo_service.index,
        ZERO_ADDRESS,
        bob_wallet,
        algo_order_requirements.computeAddress,
)

compute_inputs = [ComputeInput(DATA_did, DATA_order_tx_id, compute_service.index)]
job_id = ocean.compute.start(
    compute_inputs,
    bob_wallet,
    algorithm_did=ALG_did,
    algorithm_tx_id=ALG_order_tx_id,
    algorithm_datatoken=ALG_datatoken.address
)
print(f"Started compute job with id: {job_id}")
```

## 7. Bob monitors logs / algorithm output

In the same Python console, you can check the job status as many times as needed:

```python
ocean.compute.status(DATA_did, job_id, bob_wallet)

```

This will output the status of the current job.
Here is a list of possible results: [Operator Service Status description](https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description).

Once you get `{'ok': True, 'status': 70, 'statusText': 'Job finished'}`, Bob can check the result of the job.

```python
result = ocean.compute.result(DATA_did, job_id, 0, bob_wallet)  # 0 index, means we retrieve the results from the first dataset index

import pickle
model = pickle.loads(result)  # the gaussian model result
```

You can use the result however you like. For the purpose of this example, let's plot it.
```python
import numpy
from matplotlib import pyplot

X0_vec = numpy.linspace(-5., 10., 15)
X1_vec = numpy.linspace(0., 15., 15)
X0, X1 = numpy.meshgrid(X0_vec, X1_vec)
b, c, t = 0.12918450914398066, 1.5915494309189535, 0.039788735772973836
u = X1 - b*X0**2 + c*X0 - 6
r = 10.*(1. - t) * numpy.cos(X0) + 10
Z = u**2 + r

fig, ax = pyplot.subplots(subplot_kw={"projection": "3d"})
ax.scatter(X0, X1, model, c="r", label="model")
pyplot.title("Data + model")
pyplot.show() # or pyplot.savefig("test.png") to save the plot as a .png file instead
```

You should see something like this:

![test](https://user-images.githubusercontent.com/4101015/134895548-82e8ede8-d0db-433a-b37e-694de390bca3.png)
