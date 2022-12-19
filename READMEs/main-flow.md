<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Main flow

This step is the fun one! In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

We assume you've already [installed Ocean](install.md), [configured brownie](brownie.md), and done either [local](setup-local.md) or [remote setup](setup-remote.md).

This flow works for local _or_ remote setup, without any changes between them (!)

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

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Below, we show four possible approaches:
- A & B are when Alice is in contact with Bob. She can mint directly to him, or mint to herself and transfer to him.
- C is when Alice wants to share access for free, to anyone
- D is when Alice wants to sell access

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

Bob now has the datatoken for the dataset! Time to download the dataset and use it.

In the same Python console:
```python
# Bob sends a datatoken to the service to get access
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob_wallet)

# Bob downloads the file. If the connection breaks, Bob can try again
file_name = ocean.assets.download_asset(ddo, bob_wallet, './', order_tx_id)
```

Let's check that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

The file is in ARFF format, used by some AI/ML tools. Our example has two input variables (x0, x1) and one output.

```console
% 1. Title: Branin Function
% 3. Number of instances: 225
% 6. Number of attributes: 2

@relation branin

@attribute 'x0' numeric
@attribute 'x1' numeric
@attribute 'y' numeric

@data
-5.0000,0.0000,308.1291
-3.9286,0.0000,206.1783
...
```

## Next step

You're now done all the quickstart steps! There are many possible directions.

- You can review the appendices below to see repeat previous steps, but with further flexibility
- And you can go back to the [main README](../README.md) to learn more yet


## Appendix: Publish Details

### Publish Flexibility

Here's an example similar to above, but exposes more fine-grained control.

In the same python console:
```python
# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"
metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# Use "UrlFile" asset type. (There are other options)
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Publish data asset
from ocean_lib.ocean.ocean_assets import DatatokenArguments
_, _, ddo = ocean.assets.create(
    metadata,
    alice_wallet,
    datatoken_args=[DatatokenArguments(files=[url_file])],
)
print(f"Just published asset, with did={ddo.did}")
```

### Metadata Encryption or Compression

The asset metadata is stored on-chain. It's encrypted and compressed by default. Therefore it supports GDPR "right-to-be-forgotten" compliance rules by default.

You can control this during create():
- To disable encryption, use `ocean.assets.create(..., encrypt_flag=False)`.
- To disable compression, use `ocean.assets.create(..., compress_flag=False)`.
- To disable both, use `ocean.assets.create(..., encrypt_flag=False, compress_flag=False)`.


### Different Templates

`ocean.assets.create(...)` creates a data NFT using ERC721Template, and datatoken using ERC20Template by default. For each, you can use a different template. In creating a datatoken, you can use an existing data NFT by adding the argument `data_nft_address=<data NFT address>`.


## Appendix: Faucet Details

### Faucet Flexibility

`create_dispenser()` can take these optional arguments:
- `max_tokens` - maximum number of tokens to dispense. The default is a large number.
- `max_balance` - maximum balance of requester. The default is a large number.

A call with both would look like `create_dispenser({"from": alice_wallet}, max_tokens=max_tokens, max_balance=max_balance)`


### Faucet Tips & Tricks

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


## Appendix: Exchange Details

### Exchange Flexibility

When Alice posted the dataset for sale via `create_exchange()`, she used OCEAN. Alternatively, she could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, DAI, RAI, WETH, or other, for a slightly higher fee (0.2% vs 0.1%).


### Exchange Tips & Tricks

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
