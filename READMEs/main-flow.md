<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Main flow

This step is the fun one! In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

We assume you've already installed Ocean, configured Brownie, and done either local or remote setup.

This flow works for local or remote setup, without any changes (!)

## 1. Alice publishes dataset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice)
print(f"Just published asset, with did={ddo.did}")
```

## 2. Bob gets access to the dataset

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Below, we show four possible approaches A-D.

In the same Python console:
```python
#Approach A: Alice mints datatokens to Bob
datatoken.mint(bob, "1 ether", {"from": alice})

#Approach B: Alice mints for herself, and transfers to Bob
datatoken.mint(alice, "1 ether", {"from": alice})
datatoken.transfer(bob, "1 ether", {"from": alice})

#Approach C: Alice posts for free, via a faucet; Bob requests & gets
datatoken.create_dispenser({"from": alice})
datatoken.dispense("1 ether", {"from": bob})

#Approach D: Alice posts for sale; Bob buys
# D.1 Alice creates exchange
price = to_wei(100)
exchange = datatoken.create_exchange(price, OCEAN.address, {"from": alice})

# D.2 Alice makes 100 datatokens available on the exchange
datatoken.mint(alice_wallet, to_wei(100), {"from": alice_wallet})
datatoken.approve(exchange.address, to_wei(100), {"from": alice_wallet})

# D.3 Bob lets exchange pull the OCEAN needed 
OCEAN_needed = exchange.BT_needed(to_wei(1), consume_market_fee=0)
OCEAN.approve(exchange.address, OCEAN_needed, {"from":bob_wallet})

# D.4 Bob buys datatoken
exchange.buy_DT(to_wei(1), consume_market_fee=0, tx_dict={"from": bob_wallet})
````

## 3. Bob consumes the dataset

In the same Python console:
```python
# Bob sends a datatoken to the service to get access
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob_wallet)

# Bob downloads the file. If the connection breaks, Bob can try again
file_name = ocean.assets.download_asset(ddo, bob_wallet, './', order_tx_id)
```

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```


## Next step

You're now done all the quickstart steps! There are now many possible directions. Please go back to the [main README](README.md) to find what suits you.