<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Get Test MATIC for Mumbai

Mumbai is Polygon's testnet. It needs (fake) MATIC to pay gas for transactions.

The READMEs use one or two remote accounts, with keys `REMOTE_TEST_PRIVATE_KEY1` and `REMOTE_TEST_PRIVATE_KEY2`. This README will show how to generate these keys, related addresses, and fill them with fake MATIC.

### 1. Setup

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites

## 2. Create two new accounts (one-time)

In your console, run Python.
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

Now, you have two mumbai accounts (address & private key). Save them somewhere safe, like a local file or a password manager. They actually work on any chain, not just Mumbai.

The "export " is so that you can conveniently copy & paste them into a console, to set envvars for Ocean quickstarts or otherwise.

## 3. Get (fake) MATIC

Now, get Mumbai MATIC for each account, via a faucet:
1. Go to https://faucet.polygon.technology/. Ensure you've selected "Mumbai" network and "MATIC" token.
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2

You could got fake ETH / MATIC / etc for these accounts in other chains, by going to a faucet for each respective chain.

