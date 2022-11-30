<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Faucet to dispense free datatokens

This quickstart describes how to create a faucet to dispense free datatokens.

It focuses on Alice's experience as a publisher.

Here are the steps:

1.  Setup
2.  Alice creates a datatoken
3.  Alice creates a dispenser

Let's go through each step.

## 1. Setup

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

## 2. Publish Dataset

From [publish-flow](publish-flow.md), do:
- [x] 2. Publish dataset

Now, you have a `data_NFT`, `datatoken`, and `ddo` for the dataset.

### 3. Dispenser creation & activation

In the same Python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Key parameter
from web3.main import Web3
max_amount = Web3.toWei(50, "ether")

# Retrieve the dispenser
dispenser = ocean.dispenser

# Create dispenser
datatoken.createDispenser(
    dispenser.address,
    max_amount,
    max_amount,
    True,
    ZERO_ADDRESS,
    {"from": alice_wallet},
)

dispenser_status = dispenser.status(datatoken.address)
assert dispenser_status[0] is True
assert dispenser_status[1] == alice_wallet.address
assert dispenser_status[2] is True

initial_balance = datatoken.balanceOf(alice_wallet.address)
assert initial_balance == 0
dispenser.dispense_tokens(
    datatoken, max_amount, {"from": alice_wallet}
)
assert datatoken.balanceOf(alice_wallet.address) == max_amount
```


## Appendix. Tips & Tricks

You can combine the transactions to (a) publish data NFT, (b) publish datatoken, and (c) publish dispenser into a _single_ transaction, via the method `create_nft_erc20_with_dispenser`.


