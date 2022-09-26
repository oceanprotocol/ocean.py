<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Consume Flow

This quickstart describes how data is consumed / downloaded, including metadata.

It focuses on Alice's experience as a publisher, and Bob's experience as a consumer.

Here are the steps:

1.  Setup
2.  Alice publishes dataset
3.  Alice gives Bob access
4.  Bob downloads it

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Alice publishes dataset

Now, you're Alice. From [publish-flow](publish-flow.md), do:
- [x] 2. Publish Dataset. (This includes publishing a data NFT & datatoken)

## 3. Alice gives Bob access

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Similar to any ERC20 token, options include (a) buy a datatoken in a data market, (b) buying it over-the-counter (OTC), (c) having Alice transfer a datatoken to you (`datatoken.transfer()`), or (d) having Alice mint one into your wallet.

This README uses (d) - minting. Specifically, Alice mints a datatoken into Bob's wallet. In the same Python console:
```python
datatoken = ocean.get_datatoken(asset.datatokens[0]["address"])
datatoken.mint(
    account_address=bob_wallet.address,
    value=ocean.to_wei("1"),
    from_wallet=alice_wallet,
)
```

## 4. Bob downloads the dataset

In the same Python console:
```python
# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Bob sends 1.0 datatokens to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(asset, bob_wallet)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access! He downloads the asset. 
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
print(f"file_path = '{file_path}'")  # e.g. datafile.0xAf07...
```

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

Congrats to Bob for buying and consuming a data asset!

## Appendix: Further Flexibility

`pay_for_access_service()` fills in good defaults of using the 0th service (if >1 services available) and zero fees. Here's how it looks if we filled them explicitly.

And `download_asset()` fills in a good default for `service` too, as well as for `index` and `userdata` (not shown).

In the same python console:
```python
# Let's get more datatokens to Bob first
datatoken.mint(bob_wallet.address, ocean.to_wei("1"), alice_wallet)

# Bob retrieves the reference to the service object
service = asset.services[0]

# Bob sends 1.0 datatokens to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    bob_wallet,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken.address,
    consume_market_order_fee_amount=0,
)

# Bob now has access! He downloads the asset. 
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id,
    service=service
)
```

## Appendix: About ARFF

The file is in ARFF format, used by some AI/ML tools. In our example, it has two input variables (x0, x1) and one output.

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

