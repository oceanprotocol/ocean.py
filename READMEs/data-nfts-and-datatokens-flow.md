<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Data NFT & Datatoken

## 1. Setup
## Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

## Download barge and run services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
# The `--with-c2d` option tells barge to include the Compute-to-Data backend
./start_ocean.sh --with-c2d
```

When running barge with c2d enabled, use the following bash script to wait until
the `artifacts` directory and `address.json` file are successfully created and c2d is fully deployed:
```console
for i in $(seq 1 50); do
    sleep 5
    [ -f "$HOME/.ocean/ocean-contracts/artifacts/ready" -a -f "$HOME/.ocean/ocean/c2d/ready" ] && break
    done
```

## Install the library from v4 sources

In a new console:

```console
# Create your working directory
mkdir my_project
cd my_project

# Initialize virtual environment and activate it. Install artifacts.
python3 -m venv venv
source venv/bin/activate

# Avoid errors for the step that follows
pip3 install wheel

# Install Ocean library. Allow pre-releases to get the latest v4 version.
pip3 install --pre ocean-lib
```

## Set envvars
```console
# Set envvars
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

# Set the address file only for ganache
export ADDRESS_FILE=~/.ocean/ocean-contracts/artifacts/address.json

# Set network URL
export OCEAN_NETWORK_URL=http://127.0.0.1:8545
```

## 2. Publish Data NFT & Datatoken

### 2.1 Create a data NFT

Open a new console and run python console with the command:
```console
python
```

In the Python console:

```python
# Create Ocean instance
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)

# Publish an NFT token
data_nft = ocean.create_data_nft('NFTToken1', 'NFT1', alice_wallet)
print(f"Created data NFT. Its address is {data_nft.address}")
```

Congrats, you've created your first Ocean data NFT!

### 2.2 Create a datatoken from the data NFT

In the same python console:
```python
# Create datatoken related to the above NFT.

datatoken = data_nft.create_datatoken("Datatoken 1", "DT1", from_wallet=alice_wallet)
print(f"Created datatoken. Its address is {datatoken.address}")
```

Congrats, you've created your first Ocean datatoken! 🐋

## 3. Tips and tricks

You can combine creating a data NFT and datatoken into a single call: `ocean.create_nft_with_erc20()`.

To learn more about some of the objects you created, here are some examples.
```python
# config
print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

# wallet
print(f"alice_wallet.address = '{alice_wallet.address}'")

# data NFT
print(f"data NFT token name: {data_nft.token_name()}")
print(f"data NFT token symbol: {data_nft.symbol()}")

# datatoken
print(f"datatoken name: {datatoken.token_name()}")
print(f"datatoken symbol: {datatoken.symbol()}")
```
