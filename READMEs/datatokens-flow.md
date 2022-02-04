<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish datatoken

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

# make sure to use the dev version of the operator service URL, to match the barge provider
export OPERATOR_SERVICE_URL=https://c2d-dev.operator.oceanprotocol.com/

#run barge: start ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh  --with-provider2
```

## Install the library from v4 sources

In a new console:

```console
# Grab ocean.py repo
cd Desktop/
git clone https://github.com/oceanprotocol/ocean.py.git
git checkout v4main

# Create your working directory. Copy artifacts.
mkdir my_project
cd my_project

# Initialize virtual environment and activate it. Install artifacts.
python3 -m venv venv
source venv/bin/activate

# Intermediary installation before PyPi release of V4. Install wheel first to avoid errors.
pip3 install wheel
pip3 install --no-cache-dir ../ocean.py/
```

## Set envvars
```console
# Set envvars
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

# Set the address file only for ganache
export ADDRESS_FILE=~/.ocean/ocean-contracts/artifacts/address.json

# Set network URL
export OCEAN_NETWORK_URL=http://127.0.0.1:8545
```

## 2. Publish datatokens
Open a new console and run python console with the command:
```console
python
```

In the Python console:

```python
import os
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('TEST_PRIVATE_KEY1')
config = ExampleConfig.get_config()
ocean = Ocean(config)
print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")

print("Create wallet: begin")
wallet = Wallet(ocean.web3, private_key, config.block_confirmations, config.transaction_timeout)
print(f"Create wallet: done. Its address is {wallet.address}")

print("Create ERC721 data NFT: begin.")
erc721_token = ocean.create_nft_token(name="Dataset name", symbol="dtsymbol", from_wallet=wallet)
print(f"Created ERC721 token: done. Its address is {erc721_token.address}")
print(f"data NFT token name: {erc721_token.token_name()}")
print(f"data NFT token symbol: {erc721_token.symbol()}")

# Create ERC20 token related to the above NFT.
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

print("Create ERC20 datatoken: begin.")
cap = ocean.to_wei(10)
erc20_data = CreateErc20Data(
    template_index=1, # default value
    strings=["ERC20DT1", "ERC20DT1Symbol"], # name & symbol for ERC20 token
    addresses=[
        wallet.address, # minter address
        wallet.address, # fee manager for this ERC20 token
        wallet.address, # publishing Market Address
        ZERO_ADDRESS, # publishing Market Fee Token
    ],
    uints=[cap, 0],
    bytess=[b""]
)
nft_factory = ocean.get_nft_factory()
erc20_token = erc721_token.create_datatoken(erc20_data=erc20_data, from_wallet=wallet)
print(f"Created ERC20 datatoken: done. Its address is {erc20_token.address}")
print(f"datatoken name: {erc20_token.token_name()}")
print(f"datatoken symbol: {erc20_token.symbol()}")
```

As an alternative to publishing the nft and the datatoken using separate transactions,
you can use the `create_nft_erc_tokens_once` function to deploy them within a single
transaction. ocean.py also offers the option of creating the NFT, the ERC20 and a pool, exchange or
dispenser within the same transaction, using the PoolData, FixedData or DispenserData
as arguments.

```python
from ocean_lib.models.models_structures import CreateErc20Data, CreateERC721DataNoDeployer
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

nft_factory = ocean.get_nft_factory()

cap = ocean.to_wei(10)
erc721_data = CreateERC721DataNoDeployer(
    name="NFT",
    symbol="NFTSYMBOL",
    template_index=1,  # default value
    token_uri="https://oceanprotocol.com/nft/",
)
erc20_data = CreateErc20Data(
    template_index=1, # default value
    strings=["ERC20DT1", "ERC20DT1Symbol"], # name & symbol for ERC20 token
    addresses=[
        wallet.address, # minter address
        wallet.address, # fee manager for this ERC20 token
        wallet.address, # publishing Market Address
        ZERO_ADDRESS, # publishing Market Fee Token
    ],
    uints=[cap, 0],
    bytess=[b""]
)
erc721_token, erc20_token = nft_factory.create_nft_erc_tokens_once(
    erc721_data=erc721_data, erc20_data=erc20_data, from_wallet=wallet
)
print(f"Created ERC721 token: done. Its address is {erc721_token.address}")
print(f"data NFT token name: {erc721_token.token_name()}")
print(f"data NFT token symbol: {erc721_token.symbol()}")

print(f"Created ERC20 datatoken: done. Its address is {erc20_token.address}")
print(f"datatoken name: {erc20_token.token_name()}")
print(f"datatoken symbol: {erc20_token.symbol()}")
```


Congrats, you've created your first Ocean datatoken! 🐋
