<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Post Priced Data

This quickstart describes posting fixed-price data for sale, and subsequent purchase by others.

Here are the steps:

1.  Setup
2.  Alice publishes dataset
3.  Alice posts it for sale
4.  Bob buys dataset with OCEAN

Let's go through each step.

## 1. Setup

From [installation-flow](install.md), do:
- [x] Setup

In console, set factory envvar:
```console
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

### Create fake OCEAN

For testing purposes, we can create fake OCEAN by leveraging Ocean token factory. In the same Python console:
```python
# Mint fake OCEAN. Alice & Bob automatically get some.
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)
OCEAN = ocean.OCEAN_token

# Ensure Bob has enough funds
from brownie.network import accounts
assert accounts.at(bob_wallet.address).balance() > 0, "Bob needs ganache ETH"
assert OCEAN.balanceOf(bob_wallet.address) > 0, "Bob needs OCEAN"
```

## 2. Alice publishes dataset

In the same Python console:
```python
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
(data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice_wallet)
```


## 3. Alice posts dataset for sale

In the same Python console:
```python
# create exchange
from ocean_lib.ocean.util import to_wei, from_wei
price = to_wei(1)
exchange, _ = datatoken.create_exchange(price, OCEAN.address, {"from":alice_wallet})

# make 100 datatokens available on the exchange
datatoken.mint(alice_wallet, to_wei(100), {"from": alice_wallet})
datatoken.approve(exchange.address, to_wei(100), {"from": alice_wallet})
```

Instead of OCEAN, Alice could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, WETH, or other, for a slightly higher fee.

## 4. Bob buys dataset with OCEAN

Now, you're Bob. In the same Python console:
```python
# let exchange pull the OCEAN needed 
OCEAN_needed = exchange.BT_needed(to_wei(1), consume_market_fee=0)
OCEAN.approve(exchange.address, OCEAN_needed, {"from":bob_wallet})

# buy datatoken
exchange.buy_DT(to_wei(1), consume_market_fee=0, tx_dict={"from": bob_wallet})

# That's it! To wrap up, let's check Bob's balance
bal = datatoken.balanceOf(bob_wallet.address)
print(f"Bob has {from_wei(bal)} datatokens")
```

## Appendix. Tips & Tricks

Here's how to see all the exchanges that list the datatoken. In the Python console:
```python
exchanges = datatoken.get_exchanges() # list of OneExchange
```

To learn more about the exchange status:

```python
print(exchange.details)
print(exchange.fees_info)
```

It will output something like:
```text
>>> print(exchange.details)
ExchangeDetails: 
  datatoken = 0xdA3cf7aE9b28E1A9B5F295201d9AcbEf14c43019
  base_token = 0x24f42342C7C171a66f2B7feB5c712471bED92A97
  fixed_rate (price) = 1.0 (1000000000000000000 wei)
  active = True
  dt_supply = 99.0 (99000000000000000000 wei)
  bt_supply = 1.0 (1000000000000000000 wei)
  dt_balance = 0.0 (0 wei)
  bt_balance = 1.0 (1000000000000000000 wei)
  with_mint = False
  dt_decimals = 18
  bt_decimals = 18
  owner = 0x02354A1F160A3fd7ac8b02ee91F04104440B28E7

>>> print(exchange.fees_info)
FeesInfo: 
  publish_market_fee = 0.0 (0 wei)
  publish_market_fee_available = 0.0 (0 wei)
  publish_market_fee_collector = 0x02354A1F160A3fd7ac8b02ee91F04104440B28E7
  opc_fee = 0.001 (1000000000000000 wei)
  ocean_fee_available (to opc) = 0.001 (1000000000000000 wei)
```
