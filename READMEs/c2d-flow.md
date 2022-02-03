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

This c2d flow example features a simple algorithm from the field of ML. Ocean c2d is not limited to ML datasets and algorithms, but it is one of the most common use cases. Besides the flow below, two other worked C2D flows are:

TODO: Update these examples based on v4
1. simple image processing at [ocean-lena](https://github.com/calina-c/ocean-lena/blob/main/c2d-flow.md)
2. logistic regression for classification [blog post](https://medium.com/ravenprotocol/machine-learning-series-using-logistic-regression-for-classification-in-oceans-compute-to-data-18df49b6b165) with both GUI and CLI flows.

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

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars

### Start Python

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

## 2. Alice publishes a Data NFT

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT

## 3. Alice publishes a dataset

In the same python console:

```python
# Prepare data for ERC20 token
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
DATA_erc20_data = CreateErc20Data(
    template_index=1,
    strings=["Datatoken 1", "DT1"],
    addresses=[
        alice_wallet.address,
        alice_wallet.address,
        ZERO_ADDRESS,
        ocean.OCEAN_address,
    ],
    uints=[ocean.to_wei(100000), 0],
    bytess=[b""],
)
DATA_datatoken = DATA_nft_token.create_datatoken(DATA_erc20_data, alice_wallet)
print(f"DATA_datatoken address = '{DATA_datatoken.address}'")

# Specify metadata and services, using the Branin test dataset
DATA_date_created = "2021-12-28T10:55:11Z"
DATA_metadata = {
    "created": DATA_date_created,
    "updated": DATA_date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.agreements.file_objects import UrlFile
DATA_url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Encrypt file(s) using provider
DATA_encrypted_files = ocean.assets.encrypt_files([DATA_url_file])

# Set the compute values for compute service
DATA_compute_values = {
    "allowRawAlgorithm": False,
    "allowNetworkAccess": True,
    "publisherTrustedAlgorithms": [],
    "publisherTrustedAlgorithmPublishers": [],
}

# Create the Service
from ocean_lib.services.service import Service
DATA_compute_service = Service(
    service_id="2",
    service_type="compute",
    service_endpoint=f"{ocean.config.provider_url}/api/services/compute",
    datatoken=DATA_datatoken.address,
    files=DATA_encrypted_files,
    timeout=3600,
    compute_values=DATA_compute_values,
)

# Publish asset with compute service on-chain.
DATA_asset = ocean.assets.create(
    metadata=DATA_metadata,
    publisher_wallet=alice_wallet,
    encrypted_files=DATA_encrypted_files,
    services=[DATA_compute_service],
    erc721_address=DATA_nft_token.address,
    deployed_erc20_tokens=[DATA_datatoken],
)

print(f"DATA_asset did = '{DATA_asset.did}'")
```

## 4. Alice publishes an algorithm

For this step, there are some prerequisites needed. If you want to replace the sample algorithm with an algorithm of your choosing, you will need to do some dependency management.
You can use one of the standard [Ocean algo_dockers images](https://github.com/oceanprotocol/algo_dockers) or publish a custom docker image.

Use the image name and tag in the `container` part of the algorithm metadata.
This docker image needs to have basic support for dependency installation e.g. in the case of Python, OS-level library installations, pip installations etc.
Take a look at the [Ocean tutorials](https://docs.oceanprotocol.com/tutorials/compute-to-data-algorithms/) to learn more about docker image publishing.

Please note that this example features a simple Python algorithm. If you publish an algorithm in another language, make sure you have an appropriate container to run it, including dependencies.
You can find more information about how to do this in the [Ocean tutorials](https://docs.oceanprotocol.com/tutorials/compute-to-data-algorithms/).

In the same Python console:

```python
# Publish the algorithm NFT token
ALGO_nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
print(f"ALGO_nft_token address = '{ALGO_nft_token.address}'")

# Publish the datatoken
ALGO_erc20_data = CreateErc20Data(
    template_index=1,
    strings=["Datatoken 1", "DT1"],
    addresses=[
        alice_wallet.address,
        alice_wallet.address,
        ZERO_ADDRESS,
        ocean.OCEAN_address,
    ],
    uints=[ocean.to_wei(100000), 0],
    bytess=[b""],
)
ALGO_datatoken = ALGO_nft_token.create_datatoken(ALGO_erc20_data, alice_wallet)

# Specify metadata and services, using the Branin test dataset
ALGO_date_created = "2021-12-28T10:55:11Z"

ALGO_metadata = {
    "created": ALGO_date_created,
    "updated": ALGO_date_created,
    "description": "gpr",
    "name": "gpr",
    "type": "algorithm",
    "author": "Trent",
    "license": "CC0: PublicDomain",
    "algorithm": {
        "language": "python",
        "format": "docker-image",
        "version": "0.1",
        "container": {
            "entrypoint": "python $ALGO",
            "image": "oceanprotocol/algo_dockers",
            "tag": "python-branin",
            # TODO: fix checksum
            "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
        },
    }
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
ALGO_url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/gpr.py"
)

# Encrypt file(s) using provider
ALGO_encrypted_files = ocean.assets.encrypt_files([ALGO_url_file])

# Publish asset with compute service on-chain.
# The download (access service) is automatically created, but you can explore other options as well
ALGO_asset = ocean.assets.create(
    metadata=ALGO_metadata,
    publisher_wallet=alice_wallet,
    encrypted_files=ALGO_encrypted_files,
    erc721_address=ALGO_nft_token.address,
    deployed_erc20_tokens=[ALGO_datatoken],
)

print(f"ALGO_asset did = '{ALGO_asset.did}'")
```

## 5. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
from ocean_lib.assets.trusted_algorithms import add_publisher_trusted_algorithm
add_publisher_trusted_algorithm(DATA_asset, ALGO_asset.did, config.metadata_cache_uri)
DATA_asset = ocean.assets.update(DATA_asset, alice_wallet)
```

## 6. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
bob_wallet = Wallet(
    ocean.web3,
    os.getenv('TEST_PRIVATE_KEY2'),
    config.block_confirmations,
    config.transaction_timeout,
)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Alice mints DATA datatokens and ALGO datatokens to Bob.
# Alternatively, Bob might have bought these in a market.
DATA_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
ALGO_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
```

## 7. Bob starts a compute job

Only inputs needed: DATA_did, ALGO_did. Everything else can get computed as needed.

In the same Python console:
```python
# Convenience variables
DATA_did = DATA_asset.did
ALGO_did = ALGO_asset.did

# Operate on updated and indexed assets
DATA_asset = ocean.assets.resolve(DATA_did)
ALGO_asset = ocean.assets.resolve(ALGO_did)

compute_service = DATA_asset.get_service("compute")
algo_service = ALGO_asset.get_service("access")

from datetime import datetime, timedelta

# Pay for dataset for 1 day
DATA_order_tx_id = ocean.assets.pay_for_service(
    asset=DATA_asset,
    service=compute_service,
    wallet=bob_wallet,
    initialize_args={
        "compute_environment": "unused",
        "valid_until": int((datetime.now() + timedelta(days=1)).timestamp()),
    },
)
print(f"Paid for dataset compute service, order tx id: {DATA_order_tx_id}")

# Pay for algorithm for 1 day
ALGO_order_tx_id = ocean.assets.pay_for_service(
    asset=ALGO_asset,
    service=algo_service,
    wallet=bob_wallet,
    initialize_args={
        "valid_until": int((datetime.now() + timedelta(days=1)).timestamp()),
    }
)
print(f"Paid for algorithm access service, order tx id: {ALGO_order_tx_id}")

# Start compute job
from ocean_lib.models.compute_input import ComputeInput
DATA_compute_input = ComputeInput(DATA_did, DATA_order_tx_id, compute_service.id)
ALGO_compute_input = ComputeInput(ALGO_did, ALGO_order_tx_id, algo_service.id)
job_id = ocean.compute.start(
    consumer_wallet=bob_wallet,
    dataset=DATA_compute_input,
    # TODO: Update once compute environment implemented in provider
    compute_environment="unused",
    algorithm=ALGO_compute_input,
)
print(f"Started compute job with id: {job_id}")
```

## 8. Bob monitors logs / algorithm output

In the same Python console, you can check the job status as many times as needed:

```python
# Wait until job is done
import time
succeeded = False
for _ in range(0, 200):
    status = ocean.compute.status(DATA_did, job_id, bob_wallet)
    if status["status"] > 60:
        succeeded = True
        break
    time.sleep(5)
```

This will output the status of the current job.
Here is a list of possible results: [Operator Service Status description](https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description).

Once you get `{'ok': True, 'status': 70, 'statusText': 'Job finished'}`, Bob can check the result of the job.

```python
# Retrieve algorithm output and log files
for i in range(len(status["results"])):
    result_type = status["results"][i]["type"]
    print(f"Fetch result index {i}, type: {result_type}")
    result = ocean.compute.result(DATA_did, job_id, i, bob_wallet)
    print(result)
    print("==========\n")

    # Extract algorithm output
    if result_type == "output":
        output = result

import pickle
model = pickle.loads(output)  # the gaussian model result
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
