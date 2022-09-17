<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Get Test MATIC for Mumbai

Mumbai is Polygon's testnet. It needs (fake) MATIC to pay gas for transactions.

### 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites

## 2. Create a new address / key

In your console, run Python.
```console
python
```

In the Python console:

```python
from eth_account.account import Account
account = Account.create()
print(f"New address: {account.address}")
print(f"New private key: {account.key.hex()}")
```

## 3. Get (fake) MATIC

Now, you have two new accounts (address & private key). Same them somewhere safe, like a local file or a password manager.

Now, get Mumbai ETH for each account, via a faucet:

1. Go to https://faucet.polygon.technology/. Ensure you've selected "Mumbai" network and "MATIC" token.
2. Request funds for ADDRESS1
3. Request funds for ADDRESS2