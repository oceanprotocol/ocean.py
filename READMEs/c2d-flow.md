<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Compute-to-Data (C2D) Flow

This quickstart describes a C2D flow, using [remote services and Goerli testnet](https://docs.oceanprotocol.com/core-concepts/networks#goerli).

Here are the steps:

1. Setup
2. Alice publishes dataset
3. Alice publishes algorithm
4. Alice allows the algorithm for C2D for that data asset
5. Bob acquires datatokens for data and algorithm
6. Bob starts a compute job using a free C2D environment (no provider fees)
7. Bob monitors logs / algorithm output

Let's go through each step.

## 1. Setup

### Prerequisites & installation

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Install matplotlib

This example uses C2D to create a regression model. We'll use the library `matplotlib` to visualize it.

In the same console:
```console
#ensure you're in the Python virtualenv
source venv/bin/activate

#install matplotlib
pip install numpy matplotlib
```

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python. Includes: Config, Alice's wallet, Bob's wallet


## 2. Alice publishes dataset

In the same python console:

```python
# Publish data NFT, datatoken, and aset for dataset based on url
DATASET_url = "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/branin.arff"

name = "Branin dataset"
(DATASET_data_nft, DATASET_datatoken, DATASET_asset) = ocean.assets.create_url_asset(name, DATASET_url, alice_wallet, wait_for_aqua=True)
print(f"DATASET_data_nft address = '{DATASET_data_nft.address}'")
print(f"DATASET_datatoken address = '{DATASET_datatoken.address}'")


# Set the compute values for compute service
DATASET_compute_values = {
    "allowRawAlgorithm": False,
    "allowNetworkAccess": True,
    "publisherTrustedAlgorithms": [],
    "publisherTrustedAlgorithmPublishers": [],
}

# Create the Service
from ocean_lib.structures.file_objects import UrlFile
DATASET_compute_service = Service(
    service_id="2",
    service_type="compute",
    service_endpoint=ocean.config_dict["PROVIDER_URL"],
    datatoken=DATASET_datatoken.address,
    files=[UrlFile(url=DATASET_url)],
    timeout=3600,
    compute_values=DATASET_compute_values,
)

# Add service and update asset
DATASET_asset.add_service(DATASET_compute_service)
DATASET_asset = ocean.assets.update(DATASET_asset, alice_wallet)

print(f"DATASET_asset did = '{DATASET_asset.did}'")
```

## 3. Alice publishes an algorithm

In the same Python console:

```python
# Publish data NFT & datatoken for algorithm
ALGO_url = "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py"

name = "grp"
(ALGO_data_nft, ALGO_datatoken, ALGO_asset) = ocean.assets.create_url_asset(name, ALGO_url, alice_wallet, wait_for_aqua=True)

print(f"ALGO_data_nft address = '{ALGO_data_nft.address}'")
print(f"ALGO_datatoken address = '{ALGO_datatoken.address}'")

print(f"ALGO_asset did = '{ALGO_asset.did}'")

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

# update ALGO_Asset metadata
ALGO_asset.metadata.update(ALGO_metadata)
ALGO_asset = ocean.assets.update(
    asset=ALGO_asset, publisher_wallet=alice_wallet, provider_uri=config["PROVIDER_URL"])
    

print(f"ALGO_asset did = '{ALGO_asset.did}'")
```

## 4. Alice allows the algorithm for C2D for that data asset

In the same Python console:
```python
compute_service = DATASET_asset.services[1]
compute_service.add_publisher_trusted_algorithm(ALGO_asset)
DATASET_asset = ocean.assets.update(DATASET_asset, alice_wallet)

```

## 5. Bob acquires datatokens for data and algorithm

In the same Python console:
```python
# Alice mints DATASET datatokens and ALGO datatokens to Bob.
# Alternatively, Bob might have bought these in a market.
from web3.main import Web3
DATASET_datatoken.mint(bob_wallet.address, Web3.toWei(5, "ether"), {"from": alice_wallet})
ALGO_datatoken.mint(bob_wallet.address, Web3.toWei(5, "ether"), {"from": alice_wallet})
```

## 6. Bob starts a compute job using a free C2D environment

Only inputs needed: DATASET_did, ALGO_did. Everything else can get computed as needed.
For demo purposes, we will use the free C2D environment, which requires no provider fees.

In the same Python console:
```python
# Convenience variables
DATASET_did = DATASET_asset.did
ALGO_did = ALGO_asset.did

# Operate on updated and indexed assets
DATASET_asset = ocean.assets.resolve(DATASET_did)
ALGO_asset = ocean.assets.resolve(ALGO_did)

compute_service = DATASET_asset.services[1]
algo_service = ALGO_asset.services[0]
free_c2d_env = ocean.compute.get_free_c2d_environment(compute_service.service_endpoint)

from datetime import datetime, timedelta
from ocean_lib.models.compute_input import ComputeInput

DATASET_compute_input = ComputeInput(DATASET_asset, compute_service)
ALGO_compute_input = ComputeInput(ALGO_asset, algo_service)

# Pay for dataset and algo for 1 day
datasets, algorithm = ocean.assets.pay_for_compute_service(
    datasets=[DATASET_compute_input],
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
    status = ocean.compute.status(DATASET_asset, compute_service, job_id, bob_wallet)
    if status.get("dateFinished") and Decimal(status["dateFinished"]) > 0:
        succeeded = True
        break
    time.sleep(5)
```

This will output the status of the current job.
Here is a list of possible results: [Operator Service Status description](https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description).

Once the returned status dictionary contains the `dateFinished` key, Bob can retrieve the job results using ocean.compute.result or, more specifically, just the output if the job was successful.
For the purpose of this tutorial, let's choose the second option.

```python
# Retrieve algorithm output and log files
output = ocean.compute.compute_job_result_logs(
    DATASET_asset, compute_service, job_id, bob_wallet
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
