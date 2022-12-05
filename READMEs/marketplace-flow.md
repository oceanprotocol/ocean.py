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

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

### Create fake OCEAN

For testing purposes, we can create fake OCEAN by leveraging Ocean token factory. In the same Python console:
```python
# Set factory envvar. Staying in Python console lets you retain state from previous READMEs.
import os
os.environ['FACTORY_DEPLOYER_PRIVATE_KEY'] = '0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58'

# Mint fake OCEAN. Alice & Bob automatically get some.
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

OCEAN_token = ocean.OCEAN_token
OCEAN_address = OCEAN_token.address

# Ensure Bob has enough funds
from brownie.network import accounts
assert accounts.at(bob_wallet.address).balance() > 0, "Bob needs ganache ETH"
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "Bob needs OCEAN"
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
#mint datatokens
datatoken.mint(alice_wallet.address, "100 ether", {"from": alice_wallet})

#post for sale
price = "1 ether" #ie 1 OCEAN
amount = "100 ether"
exchange_id = datatoken.create_fixed_rate(price, OCEAN_address, amount, {"from":alice_wallet})
```

Instead of OCEAN, Alice could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, WETH, or other, for a slightly higher fee.

## 4. Bob buys dataset with OCEAN

Now, you're Bob. In the same Python console:
```python
# Bob buys a datatoken
datatoken.buy("1 ether", exchange_id, {"from": bob_wallet})

# That's it! To wrap up, let's check Bob's balance
from web3 import Web3
bal = datatoken.balanceOf(bob_wallet.address)
print(f"Bob has {Web3.fromWei(bal, 'ether')} datatokens")
```

## Appendix. Tips & Tricks

Here's how to see all the exchanges that list the datatoken. In the Python console:
```python
exchange_ids = datatoken.get_fixed_rate_exchanges() #list of exchange_id
```

To learn about an exchange's status:

```python
status = datatoken.exchange_status(exchange_id)
print(status)
```

It will output something like:
```text
FixedRateExchangeStatus:
  datatoken = 0x92cA723B61CbD933390aA58b83e1F00cedf4ebb6
  basetoken = 0x..
  price in baseToken (fixedRate) = 5 (50000000000000000000 wei)
  ...
```
