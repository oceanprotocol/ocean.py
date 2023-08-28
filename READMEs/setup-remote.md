<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Remote Setup

Here, we do setup for Mumbai, the testnet for Polygon. It's similar for other remote chains.

We assume you've already [installed Ocean](install.md).

Here, we will:
1. Configure networks
2. Create two accounts - `REMOTE_TEST_PRIVATE_KEY1` and `2`
3. Get fake MATIC on Mumbai
4. Get fake OCEAN on Mumbai
5. Set envvars
6. Set up Alice and Bob wallets in Python

Let's go!

## 1. Configure Networks

### 1.1 Setup network RPC URLs for all desired networks

All [Ocean chain deployments](https://docs.oceanprotocol.com/discover/networks) (Eth mainnet, Polygon, etc) are supported.

Export env vars of the format `NETWORKNAME_RPC_URL` e.g. `export POLYGON_RPC_URL=https://polygon-rpc.com`

In case you have an Infura project, you need to also export the `WEB3_INFURA_PROJECT_ID` variable *alongside* the base rpc urls.

#### If you do have an Infura account

- Linux & MacOS users: in console: `export WEB3_INFURA_PROJECT_ID=<your infura ID>`
- Windows: in console: `set WEB3_INFURA_PROJECT_ID=<your infura ID>`


## 2. Create EVM Accounts (One-Time)

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
REMOTE_TEST_PRIVATE_KEY1={account1.key.hex()}, ADDRESS1={account1.address}
REMOTE_TEST_PRIVATE_KEY2={account2.key.hex()}, ADDRESS2={account2.address}
""")
```

Then, hit Ctrl-C to exit the Python console.

Now, you have two EVM accounts (address & private key). Save them somewhere safe, like a local file or a password manager.

These accounts will work on any EVM-based chain: production chains like Eth mainnet and Polygon, and testnets like Goerli and Mumbai. Here, we'll use them for Mumbai.


## 3. Get (fake) MATIC on Mumbai

We need the a network's native token to pay for transactions on the network. [ETH](https://ethereum.org/en/get-eth/) is the native token for Ethereum mainnet; [MATIC](https://polygon.technology/matic-token/) is the native token for Polygon, and [(fake) MATIC](https://faucet.polygon.technology/) is the native token for Mumbai.

To get free (fake) MATIC on Mumbai:
1. Go to the faucet https://faucet.polygon.technology/. Ensure you've selected "Mumbai" network and "MATIC" token.
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported MATIC balance: `https://mumbai.polygonscan.com/address/<ADDRESS1 or ADDRESS2>`

## 4. Get (fake) OCEAN on Mumbai

[OCEAN](https://oceanprotocol.com/token) can be used as a data payment token, and locked into veOCEAN for Data Farming / curation. The READMEs show how to use OCEAN in both cases.
- OCEAN is an ERC20 token with a finite supply, rooted in Ethereum mainnet at address [`0x967da4048cD07aB37855c090aAF366e4ce1b9F48`](https://etherscan.io/token/0x967da4048cD07aB37855c090aAF366e4ce1b9F48).
- OCEAN on other production chains derives from the Ethereum mainnet OCEAN. OCEAN on Polygon (mOCEAN) is at [`0x282d8efce846a88b159800bd4130ad77443fa1a1`](https://polygonscan.com/token/0x282d8efce846a88b159800bd4130ad77443fa1a1).
- (Fake) OCEAN is on each testnet. Fake OCEAN on Mumbai is at [`0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8`](https://mumbai.polygonscan.com/token/0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8).

To get free (fake) OCEAN on Mumbai:
1. Go to the faucet https://faucet.mumbai.oceanprotocol.com/
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You can confirm receiving funds by going to the following url, and seeing your reported OCEAN balance: `https://mumbai.polygonscan.com/token/0xd8992Ed72C445c35Cb4A2be468568Ed1079357c8?a=<ADDRESS1 or ADDRESS2>`

## 5. Set envvars

As usual, Linux/MacOS needs "`export`" and Windows needs "`set`". In the console:

#### Linux & MacOS users:
```console
# For accounts: set private keys
export REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
export REMOTE_TEST_PRIVATE_KEY2=<your REMOTE_TEST_PRIVATE_KEY2>

# network rpc url, e.g.
export MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
export POLYGON_RPC_URL=https://polygon-rpc.com
```


#### Windows users:
```console
# For accounts: set private keys
set REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
set REMOTE_TEST_PRIVATE_KEY2=<your REMOTE_TEST_PRIVATE_KEY2>

# network rpc url, e.g.
set MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
set POLYGON_RPC_URL=https://polygon-rpc.com
```

Optionally, chainlist.org has other RPCs for [Mumbai](https://chainlist.org/chain/80001) and [Polygon](https://chainlist.org/chain/137).

## 6. Setup in Python

In your working console, run Python:
```console
python
```

In the Python console:
```python
# Create Ocean instance
import os
from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean
config = get_config_dict("mumbai")
ocean = Ocean(config)

# Create OCEAN object. ocean_lib knows where OCEAN is on all remote networks
OCEAN = ocean.OCEAN_token

# Create Alice's wallet
from eth_account import Account

alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice = Account.from_key(private_key=alice_private_key)
assert ocean.wallet_balance(alice) > 0, "Alice needs MATIC"
assert OCEAN.balanceOf(alice) > 0, "Alice needs OCEAN"

# Create Bob's wallet. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
bob = Account.from_key(private_key=bob_private_key)
assert ocean.wallet_balance(bob) > 0, "Bob needs MATIC"
assert OCEAN.balanceOf(bob) > 0, "Bob needs OCEAN"

# Compact wei <> eth conversion
from ocean_lib.ocean.util import to_wei, from_wei
```

If you get a gas-related error like `transaction underpriced`, you'll need to change the `priority_fee` or `max_fee`.

## Next step

You've now set up everything you need for testing on a remote chain, congrats! it's similar for any remote chain.

The next step is to walk through the [main flow](main-flow.md). In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

Because you've set up for remote, you'll be doing all these steps on the remote network.
