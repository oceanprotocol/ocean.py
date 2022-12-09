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
exchange = datatoken.create_fixed_rate(price, OCEAN.address, {"from":alice_wallet})

# make 100 datatokens available on the exchange
datatoken.mint(alice.address, to_wei(100), {"from": alice})
datatoken.approve(exchange.address, to_wei(100), {"from": alice})
```

Instead of OCEAN, Alice could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, WETH, or other, for a slightly higher fee.

## 4. Bob buys dataset with OCEAN

Now, you're Bob. In the same Python console:
```python
# let exchange pull the OCEAN needed 
OCEAN_needed = exchange.BT_needed(to_wei(1))
OCEAN.approve(exchange.address, OCEAN_needed, {"from":bob})

# buy datatoken
exchange.buy(to_wei(1), {"from": bob_wallet})

# That's it! To wrap up, let's check Bob's balance
bal = datatoken.balanceOf(bob_wallet.address)
print(f"Bob has {from_wei(bal)} datatokens")
```

## Appendix. Tips & Tricks

Here's how to see all the exchanges that list the datatoken. In the Python console:
```python
exchange_ids = datatoken.get_fixed_rate_exchanges() #list of exchange_id
```

To learn about an exchange's status:

```python
print(exchange.details)
```

It will output something like:
```text
ExchangeDetails:
  datatoken = 0x92cA723B61CbD933390aA58b83e1F00cedf4ebb6
  base_token = 0x..
  price (fixed_rate) = 5 (50000000000000000000 wei)
  ...
```
