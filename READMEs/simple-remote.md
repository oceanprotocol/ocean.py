<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: _Remotely_ Publish Data NFT & Datatoken

This quickstart is like the [simple-flow](READMEs/data-nfts-and-datatokens-flow.md), but uses [remote services and Mumbai testnet](https://docs.oceanprotocol.com/core-concepts/networks#mumbai).

Let's go through each step.

## 1. Setup

### Prerequisites & installation

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library


### Create Mumbai Accounts (One-Time)

From [get-test-MATIC](get-test-MATIC.md), do:
- [x] Create two new accounts
- [x] Get (fake) MATIC


### Set envvars

In the console:
```console
# For accounts: set private keys
export REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
export REMOTE_TEST_PRIVATE_KEY2=<your REMOTE_TEST_PRIVATE_KEY2>
```

### Setup in Python

Let's load services info and account info into Python `Config` and `Wallet` objects respectively.

In your working console, run Python:
```console
python
```

In the Python console:
```python
# Create Ocean instance
import os
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config("mumbai")
config["BLOCK_CONFIRMATIONS"] = 1 #faster
ocean = Ocean(config)

# Create Alice's wallet
import os
from brownie.network import accounts

alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice_wallet = accounts.add(alice_private_key)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "Alice needs MATIC"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
bob_wallet = accounts.add(bob_private_key)
assert bob_wallet.web3.eth.get_balance(bob_wallet.address) > 0, "Bob needs MATIC"
```


## 2. Publish Data NFT & Datatoken

From here on, the code's is the same as local.

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Publish Data NFT & Datatoken: Create a data NFT
- [x] Publish Data NFT & Datatoken: Create a datatoken from the data NFT


## Appendix. Create Private RPC account (One-Time)

Above, the config file set `network` as to a public RPC from maticvigil.com. When you run more transactions, you'll need your own private endpoint. [Alchemy](https://www.alchemy.com) is a good choice; it handles Mumbai. [Infura](https://infura.io) is also popular.

Example endpoints (fake ones):

- Alchemy for Mumbai: `https://polygon-mumbai.g.alchemy.com/v2/hFYoNzNTnbqbpi__0LS-dPTnNn`
