<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Remote

## 1. Setup

### Installation

From [install.md](install.md), do:
- [x] Setup


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

The brownie default RPCs require you to have your own infura account, and corresponding token WEB3_INFURA_PROJECT_ID.

- If you have an infura account: set the envvar `WEB3_INFURA_PROJECT_ID`
- If not: one way is to get an Infura account. Simpler yet is you can bypass the need for it, by changing to RPCs that don't need tokens. The command below replaces infura RPCs with public RPCs:

```console
sed -i 's#https://polygon-mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID#https://polygon-rpc.com/#g; s#https://polygon-mumbai.infura.io/v3/$WEB3_INFURA_PROJECT_ID#https://rpc-mumbai.maticvigil.com#g' ~/.brownie/network-config.yaml
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
from ocean_lib.web3_internal.utils import connect_to_network
connect_to_network("polygon-test")

import os
from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean
config = get_config_dict("polygon-test")
ocean = Ocean(config)

from brownie.network import accounts
accounts.clear()

# Create Alice's wallet

alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice_wallet = accounts.add(alice_private_key)
assert accounts.at(alice_wallet.address).balance() > 0, "Alice needs MATIC"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
bob_wallet = accounts.add(bob_private_key)
assert accounts.at(bob_wallet.address).balance() > 0, "Bob needs MATIC"
```

If you get a gas-related error like `transaction underpriced`,
you'll need to change the `priority_fee` or `max_fee`.
See details in [brownie docs](https://eth-brownie.readthedocs.io/en/stable/core-gas.html).


## Steps 2, 3, 4, etc

These are the same as the main local flow. Please follow them in [main-local.md](main-local.md).

