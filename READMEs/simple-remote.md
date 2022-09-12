<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: _Remotely_ Publish Data NFT & Datatoken

This quickstart is like the [simple-flow](READMEs/data-nfts-and-datatokens-flow.md), but uses [remote services and Rinkeby testnet](https://docs.oceanprotocol.com/core-concepts/networks#rinkeby).

Let's go through each step.

## 1. Setup

### Prerequisites & installation

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Set Config Values for Services

You'll need to point to a remote blockchain node to send txs to. Infura is convenient. Therefore:
- [Sign up to Infura](https://infura.io), and get an Infura project id. (If you haven't yet already.)


In your working directory, create a file `config.ini` and fill it with the following. It will use pre-existing services running for rinkeby testnet.

```text
[eth-network]
network = https://rinkeby.infura.io/v3/<your Infura project id>

[resources]
metadata_cache_uri = https://v4.aquarius.oceanprotocol.com
provider.url = https://v4.provider.rinkeby.oceanprotocol.com
```

Set envvars accordingly. In the console:
```console
# Point to this as config file
export OCEAN_CONFIG_FILE=config.ini

# Ensure that envvars don't override config file values:
unset OCEAN_NETWORK_URL METADATA_CACHE_URI AQUARIUS_URL PROVIDER_URL
```

### Create Rinkeby Accounts

Since we're using Rinkeby, you need two Rinkeby accounts TEST1 and TEST2, each with Rinkeby ETH. We'll do it via Python.

Open a new bash console and run Python:
```console
python

In the Python console:
```python
import os
from eth_account import Account
import secrets

#generate private keys. Each key is an account.
TEST_PRIVATE_KEY1 = "0x" + secrets.token_hex(32)
TEST_PRIVATE_KEY2 = "0x" + secrets.token_hex(32)

#print out
print(f"ADDRESS1={Account.from_key(TEST_PRIVATE_KEY1).address}, TEST_PRIVATE_KEY1={TEST_PRIVATE_KEY1}")
print(f"ADDRESS2={Account.from_key(TEST_PRIVATE_KEY2).address}, TEST_PRIVATE_KEY2={TEST_PRIVATE_KEY2}")

#set envvars
os.environ["TEST_PRIVATE_KEY1"] = TEST_PRIVATE_KEY1
os.environ["TEST_PRIVATE_KEY2"] = TEST_PRIVATE_KEY2
```

Now, get Rinkeby ETH for each account, via a faucet:
1. Go to https://rinkebyfaucet.com/
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2


### Setup in Python

Below, we load the set `Config` by loading `config.ini`, instead of importing `ExampleConfig`.

From the bash console:
```console
python
```

In the Python console:
```python
# Create Ocean instance
import os
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
config = Config(os.getenv('OCEAN_CONFIG_FILE')) # Load config file, versus import (
ocean = Ocean(config)

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
```


### The Rest

From here on, everything is the same as local.

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup in Python: Create Alice's wallet
- [x] Publish Data NFT & Datatoken: Create a data NFT
- [x] Publish Data NFT & Datatoken: Create a datatoken from the data NFT
