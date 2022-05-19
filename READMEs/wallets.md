<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Wallets

This page describes some basic approaches to Ethereum wallets and accounts.

All you really need is a private key. From that, you can derive the Ethereum address. An Ethereum "account" is a combination of private key and Eth address.

A "wallet" is a thing that stores private keys (and maybe signs transactions). This includes Metamask (browser plugin), Trezor (hardware wallet), and more. [Ocean docs on wallets](https://docs.oceanprotocol.com/tutorials/wallets/) has more information.

Here we describe:

1.  How to generate private keys
2.  Where to store private keys
3.  How your software might access accounts

## 1. How to generate private keys

### Generate in browser with Metamask

The datatokens tutorial described how to install Metamask, then use one the Ethereum accounts it auto-generates (along with the private key).

### Generate in Python

ocean-lib includes the [web3.py library](https://web3py.readthedocs.io/en/stable/) which can generate private keys. (Part of its [web3.py account management](https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.accounts)).

Here's how. In Python:

```python
from eth_account.account import Account
private_key = Account.create().key
```

## 2. Where to store private keys

The _whole point_ of crypto wallets is to store private keys. Wallets have various tradeoffs of cost, convienence, and security. For example, hardware wallets tend to be more secure but less convenient and not free.

It can also be useful to store private keys locally on your machine, for testing, though only with a small amount of value at stake (keep the risk down 🐙).

Do _not_ store your private keys on anything public, unless you want your tokens to disappear. For example, don't store your private keys in GitHub or expose them on frontend webpage code.

## 3. How your software might access Ethereum accounts

ocean.py suppports direct loading of the private key. Use an envvar that you copy in for a new session.

Here's an example key. From your console:

`export TEST_PRIVATE_KEY1=0xaefd8bc8725c4b3d15fbe058d0f58f4d852e8caea2bf68e0f73acb1aeec19baa`

The Ethereum address that gets computed from the example key is `0x281269C18376010B196a928c335E495bd05eC32F`.

In Python, you can create a wallet from this private key. Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps:
- [x] Setup : Prerequisites
- [x] Setup : Install the library from v4 sources

First we need an Ocean instance:

```python
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)
```

Now we can create the wallet based on the private key defined in the previous steps.

```python
import os
from ocean_lib.web3_internal.wallet import Wallet
private_key = os.getenv('TEST_PRIVATE_KEY1')
wallet = Wallet(ocean.web3, private_key, 1, 600)
```
