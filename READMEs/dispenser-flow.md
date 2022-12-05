<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Post free data

This quickstart describes how to create a faucet to dispense free datatokens.

It focuses on Alice's experience as a publisher.

Here are the steps:

1.  Setup
2.  Alice publishes dataset
3.  Alice creates a faucet
4.  Bob requests a datatoken

Let's go through each step.

## 1. Setup

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

## 2. Alice publishes dataset

In the same Python console:
```python
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
(data_NFT, datatoken, ddo) = ocean.ddo.create_url_ddo(name, url, alice_wallet)
```

## 3. Alice creates a faucet

In the same Python console:
```python
datatoken.create_dispenser({"from": alice_wallet})
```


## 4. Bob requests a datatoken

In the same Python console:
```python
datatoken.dispense("1 ether", {"from": bob_wallet})

# That's it! To wrap up, let's check Bob's balance
from web3 import Web3
bal = datatoken.balanceOf(bob_wallet.address)
print(f"Bob has {Web3.fromWei(bal, 'ether')} datatokens")
```


## Appendix: Further Flexibility

`create_dispenser()` can take these optional arguments:
- `max_tokens` - maximum number of tokens to dispense. The default is a large number.
- `max_balance` - maximum balance of requester. The default is a large number.

A call with both would look like `create_dispenser({"from": alice_wallet}, max_tokens=max_tokens, max_balance=max_balance)`

To learn about dispenser status:

```python
status = datatoken.dispenser_status()
print(f"For datatoken {datatoken.address}:")
print(status)
```

It will output something like:
```text
For datatoken 0x92cA723B61CbD933390aA58b83e1F00cedf4ebb6:
DispenserStatus:
  active = True
  owner_address = 0x1234
  is_minter = True
  max_tokens = 1000 (10000000000000000000000 wei)
  max_balance = 10  (100000000000000000000 wei)
  balance = 1
  allowed_swapper = anyone can request
```
