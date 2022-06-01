<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Dispenser Flow

This quickstart describes the dispenser flow.

It focuses on Alice's experience as a publisher.

Here are the steps:

1.  Setup
2.  Alice creates a datatoken
3.  Dispenser creation & activation

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources


### Set envvars

Set the required enviroment variables as described in [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Publish Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create a data NFT
- [x] 2.2 Create a datatoken from the data NFT

### 3. Dispenser creation & activation

In the same python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Get the dispenser
dispenser = ocean.dispenser

max_amount = ocean.to_wei(50)
# Create dispenser
datatoken.create_dispenser(
    dispenser_address=dispenser.address,
    max_balance=max_amount,
    max_tokens=max_amount,
    with_mint=True,
    allowed_swapper=ZERO_ADDRESS,
    from_wallet=alice_wallet,
)

dispenser_status = dispenser.status(datatoken.address)
assert dispenser_status[0] is True
assert dispenser_status[1] == alice_wallet.address
assert dispenser_status[2] is True

initial_balance = datatoken.balanceOf(alice_wallet.address)
assert initial_balance == 0
dispenser.dispense_tokens(
    datatoken=datatoken, amount=max_amount, consumer_wallet=alice_wallet
)
assert datatoken.balanceOf(alice_wallet.address) == max_amount
```

As an alternative for publishing a NFT, a datatoken and a dispenser at once, you can use `create_nft_erc20_with_dispenser`.


