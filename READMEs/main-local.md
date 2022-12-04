<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Local

## 1. Installation

From [installation-flow](install.md), do:
- [x] Setup

## 1. Setup in Python

In the same console, run Python console:
```console
python
```

In the Python console:
```python
# Create Ocean instance
from ocean_lib.web3_internal.utils import connect_to_network
connect_to_network("development")

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config("development")
ocean = Ocean(config)

# Create Alice's wallet
import os
from brownie.network import accounts
accounts.clear()
alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
alice_wallet = accounts.add(alice_private_key)

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = accounts.add(bob_private_key)
assert accounts.at(bob_wallet.address).balance() > 0, "Bob needs ganache ETH"

# Create fake OCEAN. Alice & Bob automatically get some.
import os
os.environ['FACTORY_DEPLOYER_PRIVATE_KEY'] = '0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58'
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)
OCEAN_token = ocean.OCEAN_token
```

## 1. Alice publishes dataset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data NFT & datatoken & DDO asset
(data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice_wallet)
print(f"Just published asset, with did={ddo.did}")
```

### 1. Bob gets access to the dataset

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Below, we show four possible approaches.

In the same Python console:
```python
#Approach 1: Alice mints datatokens to Bob
datatoken.mint(bob_wallet.address, "1 ether", {"from": alice_wallet})

#Approach 2: Alice mints for herself, and transfers to Bob
datatoken.mint(alice_wallet.address, "1 ether", {"from": alice_wallet})
datatoken.transfer(bob_wallet.address, "1 ether", {"from": alice_wallet})

#Approach 3: Alice posts for free, via a faucet; Bob requests & gets
datatoken.create_dispenser({"from": alice_wallet})
datatoken.dispense("1 ether", {"from": bob_wallet})

#Approach 4: Alice posts for sale; Bob buys
exchange_id = ocean.create_fixed_rate(
    datatoken, OCEAN_token, 
    amount=Web3.toWei(100, "ether"),
    fixed_rate=Web3.toWei(1, "ether"),
    from_wallet=alice_wallet,
)
OCEAN_token.approve(ocean.fixed_rate_exchange.address, "100 ether", {"from": bob_wallet})
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
tx_result = ocean.fixed_rate_exchange.buyDT(
    exchange_id,
    Web3.toWei(20, "ether"),
    Web3.toWei(50, "ether"),
    ZERO_ADDRESS,
    0,
    {"from": bob_wallet},
)
````


### 1. Bob consumes the dataset

In the same Python console:
```python
# Bob sends a datatoken to the service to get access; then downloads
file_name = ocean.assets.download_file(ddo.did, bob_wallet)
```

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```