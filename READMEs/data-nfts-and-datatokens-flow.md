<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Data NFT & Datatoken

## 1. Setup
From [install.md](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

### 🐍 Setup in Python

In the same console, run Python console:
```console
python
```

In the Python console:
```python
# Create Ocean instance
from ocean_lib.web3_internal.utils import connect_to_network
connect_to_network("development")

from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean
config = get_config_dict("development")
ocean = Ocean(config)

# Create Alice's wallet
import os
from brownie.network import accounts
accounts.clear()
alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
alice = accounts.add(alice_private_key)

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob = accounts.add(bob_private_key)
assert accounts.at(bob.address).balance() > 0, "Bob needs ganache ETH"
```

## 2. Publish Data NFT & Datatoken

### 2.1 🪄 Create a data NFT

In the same Python console:
```python
from ocean_lib.models.arguments import DataNFTArguments
data_nft = ocean.data_nft_factory.create(DataNFTArguments('NFT1', 'NFT1'), alice)
print(f"Created data NFT. Its address is {data_nft.address}")
```

Congrats, you've created your first Ocean data NFT!

### 2.2 🎉 Create a datatoken from the data NFT

By default, the template index is 1 *(regular datatoken), but use the template_index function
argument to control that (e.g. template_index=2 for an Enterprise Datatoken).

In the same Python console:
```python
# Create datatoken related to the above NFT.
from ocean_lib.models.arguments import DatatokenArguments
datatoken = data_nft.create_datatoken(DatatokenArguments("Datatoken 1", "DT1"), alice)
print(f"Created datatoken. Its address is {datatoken.address}")
```

Congrats, you've created your first Ocean datatoken! 🐋

## Appendix. Tips & Tricks

You can combine creating a data NFT and datatoken into a single call: `ocean.data_nft_factory.create_with_erc20()`.

To learn more about some of the objects you created, here are some examples.
```python
# config
print(f"config.metadata_cache_uri = {config['METADATA_CACHE_URI']}")
print(f"config.provider_url = {config['PROVIDER_URL']}")

# wallet
print(f"alice.address = '{alice_wallet.address}'")

# data NFT
print(f"data NFT name: {data_nft.name()}")
print(f"data NFT symbol: {data_nft.symbol()}")

# datatoken
print(f"datatoken name: {datatoken.name()}")
print(f"datatoken symbol: {datatoken.symbol()}")
```
