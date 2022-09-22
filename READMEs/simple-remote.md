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

### Create Config File for Services

In your working directory, create a file `myconfig.ini` and fill it with the following. It will use pre-existing services running for mumbai testnet.

```text
[eth-network]
network_name = mumbai
network = https://rpc-mumbai.maticvigil.com
address.file = ~/.ocean/ocean-contracts/artifacts/address.json
block_confirmations = 0

[resources]
metadata_cache_uri = https://v4.aquarius.oceanprotocol.com
provider.url = https://v4.provider.mumbai.oceanprotocol.com
```

### Set envvars

In the console:
```console
# For services: point to config file
export OCEAN_CONFIG_FILE=myconfig.ini

# For services: ensure no other envvars that override config file values
unset OCEAN_NETWORK_URL METADATA_CACHE_URI AQUARIUS_URL PROVIDER_URL

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
config = ExampleConfig.get_config()
ocean = Ocean(config)

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet

alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "Alice needs MATIC"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
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
- Infura for Rinkeby: `https://rinkeby.infura.io/v3/8239a2e4b8441b96aa4ae2e94aSDJFAD`
