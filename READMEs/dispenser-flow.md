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

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources


### Set envvars

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Publish Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT
- [x] 2.2 Create and erc20 datatoken from the data NFT

### 3. Dispenser creation & activation

In the same python console:
```python
from ocean_lib.models.models_structures import DispenserData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Get the dispenser
dispenser = ocean.dispenser

max_amount = ocean.to_wei(50)
dispenser_data = DispenserData(
    dispenser_address=dispenser.address,
    max_balance=max_amount,
    max_tokens=max_amount,
    with_mint=True,
    allowed_swapper=ZERO_ADDRESS,
)

# Create dispenser
erc20_token.create_dispenser(dispenser_data, from_wallet=alice_wallet)

dispenser_status = dispenser.status(erc20_token.address)
assert dispenser_status[0] is True
assert dispenser_status[1] == alice_wallet.address
assert dispenser_status[2] is True

initial_balance = erc20_token.balanceOf(alice_wallet.address)
assert initial_balance == 0
dispenser.dispense_tokens(
    erc20_token=erc20_token, amount=max_amount, consumer_wallet=alice_wallet
)
assert erc20_token.balanceOf(alice_wallet.address) == max_amount
```

As an alternative to publishing the nft, the datatoken and the dispenser using separate transactions,
you can use the `create_nft_erc_dispenser_in_one_call` function to deploy them within a single
transaction. ocean.py also offers the option of creating the NFT, the ERC20 and a pool, exchange or
dispenser within the same transaction, using the PoolData, FixedData or DispenserData
as arguments.

```python
from ocean_lib.models.models_structures import CreateErc20Data, CreateERC721DataNoDeployer, DispenserData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

nft_factory = ocean.get_nft_factory()
dispenser_address = ocean.dispenser.address

cap = ocean.to_wei(10)
erc721_data = CreateERC721DataNoDeployer(
    name="NFT",
    symbol="NFTSYMBOL",
    template_index=1,  # default value
    token_uri="https://oceanprotocol.com/nft/",
)
erc20_data = CreateErc20Data(
    template_index=1, # default value
    strings=["ERC20DT1", "ERC20DT1Symbol"], # name & symbol for ERC20 token
    addresses=[
        alice_wallet.address, # minter address
        alice_wallet.address, # fee manager for this ERC20 token
        alice_wallet.address, # publishing Market Address
        ZERO_ADDRESS, # publishing Market Fee Token
    ],
    uints=[cap, 0],
    bytess=[b""]
)

dispenser_data = DispenserData(
    dispenser_address=dispenser_address,
    max_tokens=ocean.to_wei("1"),
    max_balance=ocean.to_wei("1"),
    with_mint=True,
    allowed_swapper=ZERO_ADDRESS,
)
erc721_token, erc20_token = nft_factory.create_nft_erc_dispenser_in_one_call(
    erc721_data=erc721_data,
    erc20_data=erc20_data,
    dispenser_data=dispenser_data,
    from_wallet=alice_wallet,
)
print(f"Created ERC721 token: done. Its address is {erc721_token.address}")
print(f"data NFT token name: {erc721_token.token_name()}")
print(f"data NFT token symbol: {erc721_token.symbol()}")

print(f"Created ERC20 datatoken: done. Its address is {erc20_token.address}")
print(f"datatoken name: {erc20_token.token_name()}")
print(f"datatoken symbol: {erc20_token.symbol()}")

dispenser_status = ocean.dispenser.status(erc20_token.address)
assert dispenser_status[0] is True
assert dispenser_status[1] == nft_factory.address
assert dispenser_status[2] is True

```


