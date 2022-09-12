<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Compute-to-Data (C2D) Flow

This quickstart describes a C2D flow, using [remote services and Rinkeby testnet](https://docs.oceanprotocol.com/core-concepts/networks#rinkeby).

Here are the steps:

1. Setup
2. Alice publishes dataset
3. Alice publishes algorithm
4. Alice allows the algorithm for C2D for that data asset
5. Bob acquires datatokens for data and algorithm
6. Bob starts a compute job using a free C2D environment (no provider fees)
7. Bob monitors logs / algorithm output
8. Tips and tricks

Let's go through each step.

## 1. Setup

### Prerequisites & basic install

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Install matplotlib

This example uses C2D to create a regression model. We'll use the library `matplotlib` to visualize it. So, in the same console:
```console
pip install numpy matplotlib
```

### Set config values for the services

In your working directory, in the console:
```console

# Create and fill config.ini file:
echo "
[eth-network]
network = https://rinkeby.infura.io/v3/9aa3d95b3bc440fa88ea12eaa445616

[resources]
metadata_cache_uri = https://v4.aquarius.oceanprotocol.com
provider.url = https://v4.provider.rinkeby.oceanprotocol.com
" > config.ini

# Point to this as config file
export OCEAN_CONFIG_FILE=config.ini

# Ensure that envvars don't override config file values:
unset OCEAN_NETWORK_URL METADATA_CACHE_URI AQUARIUS_URL PROVIDER_URL
```

### Set up Rinkeby accounts

Since we're using Rinkeby, you need two Rinkeby accounts TEST1 and TEST2, each with Rinkeby ETH.

Here's one way.

1. [Install Metamask](https://metamask.io/download/) in your browser (if needed)
2. [Add Rinkeby to Metamask](https://motivationgrid.com/how-to-add-rinkeby-to-metamask-guide-with-images-updated-2022/).
3. [Create a new account](https://metamask.zendesk.com/hc/en-us/articles/360015289452-How-to-create-an-additional-account-in-your-wallet), call it "TEST1"
4. [Copy your account's address](https://metamask.zendesk.com/hc/en-us/articles/360015488791-How-to-view-your-account-details-public-address). Save it to a local text file or somewhere else safe.
5. [Get some free Rinkeby ETH via a faucet](https://rinkebyfaucet.com/). You'll need to enter your account's address. 
6. [Export your account's private key](https://metamask.zendesk.com/hc/en-us/articles/360015289632-How-to-export-an-account-s-private-key). Save it to a local text file or somewhere else safe.
7. Repeat steps 3-6, for a new account called "TEST2".

### Set envvars based on Rinkeby accounts

In the console:

```console
# Set envvars
export TEST_PRIVATE_KEY1=<private key for TEST1>
export TEST_PRIVATE_KEY2=<private key for TEST2>
```

### Setup in Python

Open a new console and run Python console:
```console
python
```

In the Python console:
```python

# Import and configure the components / services:
import os
from ocean_lib.config import Config
config = Config(os.getenv('OCEAN_CONFIG_FILE'))
ocean = Ocean(config)

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
```

## 2. Alice publishes dataset

In the same python console:

```python
# Publish the datatoken
DATA_datatoken = data_nft.create_datatoken("DATA 1", "D1", from_wallet=alice_wallet)
print(f"DATA_datatoken address = '{DATA_datatoken.address}'")

# Specify metadata and services for the Branin test dataset
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

# ocean.py offers multiple file object types. A simple url file is be enough for here
from ocean_lib.structures.file_objects import UrlFile
DATA_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/branin.arff"
)

DATA_files = [DATA_url_file]

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
    service_endpoint=ocean.config.provider_url,
    datatoken=DATA_datatoken.address,
    files=DATA_files,
    timeout=3600,
    compute_values=DATA_compute_values,
)

# Publish asset with compute service on-chain
DATA_asset = ocean.assets.create(
    metadata=DATA_metadata,
    publisher_wallet=alice_wallet,
    files=DATA_files,
    services=[DATA_compute_service],
    data_nft_address=data_nft.address,
    deployed_datatokens=[DATA_datatoken],
)

print(f"DATA_asset did = '{DATA_asset.did}'")
```

## 3. Alice publishes an algorithm

In the same Python console:

```python
# Publish the algorithm NFT token
ALGO_nft_token = ocean.create_data_nft("NFT1", "NFT1", alice_wallet)
print(f"ALGO_nft_token address = '{ALGO_nft_token.address}'")

# Publish the datatoken
ALGO_datatoken = ALGO_nft_token.create_datatoken("ALGO 1", "A1", from_wallet=alice_wallet)
print(f"ALGO_datatoken address = '{ALGO_datatoken.address}'")

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
            "checksum": "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
        },
    }
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
ALGO_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py"
)

ALGO_files = [ALGO_url_file]

# Publish asset with compute service on-chain.
# The download (access service) is automatically created, but you can explore other options as well
ALGO_asset = ocean.assets.create(
    metadata=ALGO_metadata,
    publisher_wallet=alice_wallet,
    files=ALGO_files,
    data_nft_address=ALGO_nft_token.address,
    deployed_datatokens=[ALGO_datatoken],
)

print(f"ALGO_asset did = '{ALGO_asset.did}'")
```

## 4. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
compute_service = DATA_asset.services[0]
compute_service.add_publisher_trusted_algorithm(ALGO_asset)
DATA_asset = ocean.assets.update(DATA_asset, alice_wallet)
```

## 5. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
bob_wallet = Wallet(
    ocean.web3,
    os.getenv("TEST_PRIVATE_KEY2"),
    config.block_confirmations,
    config.transaction_timeout,
)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Alice mints DATA datatokens and ALGO datatokens to Bob.
# Alternatively, Bob might have bought these in a market.
DATA_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
ALGO_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
```

## 6. Bob starts a compute job using a free C2D environment

Only inputs needed: DATA_did, ALGO_did. Everything else can get computed as needed.
For demo purposes, we will use the free C2D environment, which requires no provider fees.

In the same Python console:
```python
# Convenience variables
DATA_did = DATA_asset.did
ALGO_did = ALGO_asset.did

# Operate on updated and indexed assets
DATA_asset = ocean.assets.resolve(DATA_did)
ALGO_asset = ocean.assets.resolve(ALGO_did)

compute_service = DATA_asset.services[0]
algo_service = ALGO_asset.services[0]
free_c2d_env = ocean.compute.get_free_c2d_environment(compute_service.service_endpoint)

from datetime import datetime, timedelta
from ocean_lib.models.compute_input import ComputeInput

DATA_compute_input = ComputeInput(DATA_asset, compute_service)
ALGO_compute_input = ComputeInput(ALGO_asset, algo_service)

# Pay for dataset and algo for 1 day
datasets, algorithm = ocean.assets.pay_for_compute_service(
    datasets=[DATA_compute_input],
    algorithm_data=ALGO_compute_input,
    consume_market_order_fee_address=bob_wallet.address,
    wallet=bob_wallet,
    compute_environment=free_c2d_env["id"],
    valid_until=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
    consumer_address=free_c2d_env["consumerAddress"],
)
assert datasets, "pay for dataset unsuccessful"
assert algorithm, "pay for algorithm unsuccessful"

# Start compute job
job_id = ocean.compute.start(
    consumer_wallet=bob_wallet,
    dataset=datasets[0],
    compute_environment=free_c2d_env["id"],
    algorithm=algorithm,
)
print(f"Started compute job with id: {job_id}")
```

## 7. Bob monitors logs / algorithm output

In the same Python console, you can check the job status as many times as needed:

```python
# Wait until job is done
import time
from decimal import Decimal
succeeded = False
for _ in range(0, 200):
    status = ocean.compute.status(DATA_asset, compute_service, job_id, bob_wallet)
    if status.get("dateFinished") and Decimal(status["dateFinished"]) > 0:
        succeeded = True
        break
    time.sleep(5)
```

This will output the status of the current job.
Here is a list of possible results: [Operator Service Status description](https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description).

Once the returned status dictionary contains the `dateFinished` key, Bob can retrieve the job results using ocean.compute.result or, more specifically, just the output if the job was successful.
For the purpose of this tutorial, let us choose the second option.

```python
# Retrieve algorithm output and log files
output = ocean.compute.compute_job_result_logs(
    DATA_asset, compute_service, job_id, bob_wallet
)[0]

import pickle
model = pickle.loads(output)  # the gaussian model result
assert len(model) > 0, "unpickle result unsuccessful"
```

You can use the result however you like. For the purpose of this example, let's plot it.

```python
import numpy
from matplotlib import pyplot

X0_vec = numpy.linspace(-5., 10., 15)
X1_vec = numpy.linspace(0., 15., 15)
X0, X1 = numpy.meshgrid(X0_vec, X1_vec)
b, c, t = 0.12918450914398066, 1.5915494309189535, 0.039788735772973836
u = X1 - b * X0 ** 2 + c * X0 - 6
r = 10. * (1. - t) * numpy.cos(X0) + 10
Z = u ** 2 + r

fig, ax = pyplot.subplots(subplot_kw={"projection": "3d"})
ax.scatter(X0, X1, model, c="r", label="model")
pyplot.title("Data + model")
pyplot.show()  # or pyplot.savefig("test.png") to save the plot as a .png file instead
```

You should see something like this:

![test](https://user-images.githubusercontent.com/4101015/134895548-82e8ede8-d0db-433a-b37e-694de390bca3.png)

## Appendix. Tips & tricks

This README has a simple ML algorithm. However, Ocean C2D is not limited to usage in ML. The file [c2d-flow-more-examples.md](https://github.com/oceanprotocol/ocean.py/blob/v4main/READMEs/c2d-flow-more-examples.md) has examples from vision and other fields.

In the "publish algorithm" step, to replace the sample algorithm with another one:

- Use one of the standard [Ocean algo_dockers images](https://github.com/oceanprotocol/algo_dockers) or publish a custom docker image.
- Use the image name and tag in the `container` part of the algorithm metadata.
- The image must have basic support for installing dependencies. E.g. "pip" for the case of Python. You can use other languages, of course.
- More info: https://docs.oceanprotocol.com/tutorials/compute-to-data-algorithms/)

The function to `pay_for_compute_service` automates order starting, order reusing and performs all the necessary Provider and on-chain requests.
It modifies the contents of the given ComputeInput as follows:

- If the dataset/algorithm contains a `transfer_tx_id` property, it will try to reuse that previous transfer id. If provider fees have expired but the order is still valid, then the order is reused on-chain.
- If the dataset/algorithm does not contain a `transfer_tx_id` or the order has expired (based on the Provider's response), then one new order will be created.

This means you can reuse the same ComputeInput and you don't need to regenerate it everytime it is sent to `pay_for_compute_service`. This step makes sure you are not paying unnecessary or duplicated fees.

If you wish to upgrade the compute resources, you can use any (paid) C2D environment.
Inspect the results of `ocean.ocean_compute.get_c2d_environments(service.service_endpoint)` and `ocean.retrieve_provider_fees_for_compute(datasets, algorithm_data, consumer_address, compute_environment, duration)` for a preview of what you will pay.
Don't forget to handle any minting, allowance or approvals on the desired token to ensure transactions pass.
