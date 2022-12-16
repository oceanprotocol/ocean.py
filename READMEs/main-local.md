<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Local

## 1. Setup

### Installation

From [install.md](install.md), do:
- [x] Setup

### Setup in Python

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
config = ExampleConfig.get_config("development")

from ocean_lib.ocean.ocean import Ocean
ocean = Ocean(config)
OCEAN = ocean.OCEAN_token

# Create Alice's wallet
import os
from brownie.network import accounts
accounts.clear()

alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
alice = accounts.add(alice_private_key)
assert accounts.at(alice).balance() > 0, "Alice needs ganache ETH"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob = accounts.add(bob_private_key)
assert accounts.at(bob).balance() > 0, "Bob needs ganache ETH"

# Mint fake OCEAN to Alice & Bob
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

# Compact wei <> eth conversion
from ocean_lib.ocean.util import to_wei, from_wei
```

## 2. Alice publishes dataset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice)
print(f"Just published asset, with did={ddo.did}")
```

### 3. Bob gets access to the dataset

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Below, we show four possible approaches A-D.

In the same Python console:
```python
#Approach A: Alice mints datatokens to Bob
datatoken.mint(bob, "1 ether", {"from": alice})

#Approach B: Alice mints for herself, and transfers to Bob
datatoken.mint(alice, "1 ether", {"from": alice})
datatoken.transfer(bob, "1 ether", {"from": alice})

#Approach C: Alice posts for free, via a faucet; Bob requests & gets
datatoken.create_dispenser({"from": alice})
datatoken.dispense("1 ether", {"from": bob})

#Approach D: Alice posts for sale; Bob buys
# D.1 Alice creates exchange
price = to_wei(100)
exchange = datatoken.create_exchange(price, OCEAN.address, {"from": alice})

# D.2 Alice makes 100 datatokens available on the exchange
datatoken.mint(alice_wallet, to_wei(100), {"from": alice_wallet})
datatoken.approve(exchange.address, to_wei(100), {"from": alice_wallet})

# D.3 Bob lets exchange pull the OCEAN needed 
OCEAN_needed = exchange.BT_needed(to_wei(1), consume_market_fee=0)
OCEAN.approve(exchange.address, OCEAN_needed, {"from":bob_wallet})

# D.4 Bob buys datatoken
exchange.buy_DT(to_wei(1), consume_market_fee=0, tx_dict={"from": bob_wallet})
````


### 4. Bob consumes the dataset

In the same Python console:
```python
# Bob sends a datatoken to the service to get access
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob_wallet)

# Bob downloads the file. If the connection breaks, Bob can try again
file_name = ocean.assets.download_asset(ddo, bob_wallet, './', order_tx_id)
```

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```