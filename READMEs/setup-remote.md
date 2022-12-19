<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Remote Setup

Here, we do setup for Mumbai, the testnet for Polygon. It's similar for other remote chains.

We assume you've already [installed Ocean](install.md), and [configured brownie](brownie.md).

What we'll do specifically:
- create two accounts, defined by `REMOTE_TEST_PRIVATE_KEY1` and `2`
- fill the accounts with fake MATIC, to pay for txs; and with fake OCEAN, to pay for data
- in Python, set up Alice and Bob's wallets using the new private keys


## 1. Create Remote Accounts (One-Time)

An EVM account is singularly defined by its private key. Its address is a function of that key. Let's generate two accounts!

In a new or existing console, run Python.
```console
python
```

In the Python console:

```python
from eth_account.account import Account
account1 = Account.create()
account2 = Account.create()

print(f"""
export REMOTE_TEST_PRIVATE_KEY1={account1.key.hex()}
export REMOTE_TEST_PRIVATE_KEY2={account2.key.hex()}

export ADDRESS1={account1.address}
export ADDRESS2={account2.address}
""")
```

Then, hit Ctrl-C to exit the Python console.

Now, you have two EVM accounts (address & private key). Save them somewhere safe, like a local file or a password manager. 

These accounts will work on any EVM-based chain: production chains like Eth mainnet and Polygon, and testnets like Goerli and Mumbai. Here, we'll use them for Mumbai.

The "export " is so that you can conveniently copy & paste them into a console, to set envvars for Ocean quickstarts or otherwise.


## 3. Get (fake) MATIC on Mumbai

We need the a network's native token to pay for transactions on the network. [ETH](https://ethereum.org/en/get-eth/) is the native token for Ethereum mainnet; [MATIC](https://polygon.technology/matic-token/) is the native token for Polygon, and [(fake) MATIC](https://faucet.polygon.technology/) is the native token for Mumbai.

To get free (fake) MATIC on Mumbai:
1. Go to the faucet https://faucet.polygon.technology/. Ensure you've selected "Mumbai" network and "MATIC" token.
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported MATIC balance: `https://mumbai.polygonscan.com/<ADDRESS1 or ADDRESS2>`

## 4. Get (fake) OCEAN on Mumbai

[OCEAN](https://oceanprotocol.com/token) can be used as a data payment token, and locked into veOCEAN for Data Farming / curation. The READMEs show how to use OCEAN in both cases.
- OCEAN is an ERC20 token with a finite supply, rooted in Ethereum mainnet at address [0x967da4048cD07aB37855c090aAF366e4ce1b9F48](https://etherscan.io/token/0x967da4048cD07aB37855c090aAF366e4ce1b9F48).
- OCEAN on other production chains derives from the Ethereum mainnet OCEAN. OCEAN on Polygon (mOCEAN) is at [0x282d8efce846a88b159800bd4130ad77443fa1a1](https://polygonscan.com/token/0x282d8efce846a88b159800bd4130ad77443fa1a1). 
- (Fake) OCEAN is on each testnet. Fake OCEAN on Mumbai is at [0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8](https://mumbai.polygonscan.com/token/0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8).

To get free (fake) OCEAN on Mumbai:
1. Go to the faucet https://faucet.mumbai.oceanprotocol.com/
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported OCEAN balance: `https://mumbai.polygonscan.com/token/0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8?a=<ADDRESS1 or ADDRESS2>`

## 5. Set envvars

In the console:
```console
# For accounts: set private keys
export REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
export REMOTE_TEST_PRIVATE_KEY2=<your REMOTE_TEST_PRIVATE_KEY2>
```

## 6. Setup in Python

In your working console, run Python:
```console
python
```

In the Python console:
```python
# Create Ocean instance
from ocean_lib.web3_internal.utils import connect_to_network
connect_to_network("polygon-test") # mumbai is "polygon-test"

import os
from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean
config = get_config_dict("polygon-test")
ocean = Ocean(config)

from ocean_lib.ocean.ocean import Ocean
ocean = Ocean(config)

# Create OCEAN object. ocean_lib knows where OCEAN is on all remote networks 
OCEAN = ocean.OCEAN_token

# Create Alice's wallet
from brownie.network import accounts
accounts.clear()

alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice_wallet = accounts.add(alice_private_key)
assert accounts.at(alice).balance() > 0, "Alice needs MATIC"
assert OCEAN.balanceOf(alice) > 0, "Alice needs OCEAN"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
bob = accounts.add(bob_private_key)
assert accounts.at(bob).balance() > 0, "Bob needs MATIC"
assert OCEAN.balanceOf(bob) > 0, "Bob needs OCEAN"
```

If you get a gas-related error like `transaction underpriced`, you'll need to change the `priority_fee` or `max_fee`. See details in [brownie docs](https://eth-brownie.readthedocs.io/en/stable/core-gas.html).


## Next step

You've now set up everything you need for testing on a remote chain, congrats! it's similar for any remote chain.

The next step - the fun one - is to walk through the [main flow](main-flow.md). In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

Because you've set up for remote, you'll be doing all these steps on the remote network.
