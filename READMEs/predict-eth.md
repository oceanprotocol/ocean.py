<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It runs on Mumbai.

Here are the steps:

1.  Setup
2.  Bob gets data locally from assets on Ocean
  2.1  Bob gets recent historical data from Binance ETH API
  2.2  Bob gets older historical data from a CSV file
3.  Bob makes predictions :
  3.1  Bob builds a simple AI model
  3.2  Bob runs the AI model to make future ETH price predictions
4.  Bob publishes the predictions as an Ocean asset
5.  Bob gives competition organizers access to the predictions

## 1. Setup

### Prerequisites & installation

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python: Create Ocean instance

We're Bob this flow. So we don't need to set up Alice's wallet.

From [c2d-flow](c2d-flow.md), do:
- [x] Setup Bob's Wallet

## 2.  Bob gets data locally from assets on Ocean

### 2.1  Bob gets recent historical data from Binance ETH APIs

In the same Python console:
```python
# With did of Binance API asset, Bob retrieves the Asset, data_nft, and datatoken objects
asset_did = <copy and paste from where you have it. E.g. from Ocean Market or publish-asset.md>

asset = ocean.assets.resolve(asset_did)
data_nft = asset.nft
datatoken = asset.datatokens[0]

print(f"Asset retrieved, with name: {data_nft.token_name()}")
print(f"  did: {asset.did}")
print(f"  data_NFT.address: {data_nft.address}")
print(f"  datatoken.address: {datatoken.address}")

# Bob gets an access token from the dispenser
amt_dispense = 1
ocean.dispenser.dispense_tokens(
    datatoken=datatoken, amount=ocean.to_wei(amt_dispense), consumer_wallet=bob_wallet
)
bal = ocean.from_wei(datatoken.balanceOf(bob_wallet.address))
print(f"Bob now holds {bal} access tokens for the data asset.")


# Bob sends 1.0 datatokens to the service, to get access
service = asset.services[0] #retrieve service object
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken.address,
    consume_market_order_fee_amount=0,
    wallet=bob_wallet,
)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access! He downloads the asset.
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    service=service,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
print(f"file_path = '{file_path}'")  # e.g. datafile.0xAf07...
```

The file downloaded is a .json. From that, use the python `json` library to parse it as desired.)

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

Congrats to Bob for buying and consuming a data asset!


###  2.2  Bob gets older historical data from a CSV file

## 3.  Bob makes predictions

### 3.1  Bob builds a simple AI model

He does this locally (client-side) in this flow. (Alternative: use C2D.)

### 3.2  Bob runs the AI model to make future ETH price predictions

Predictions are for a near-future 24h period, one prediction every hour on the hour.

## 4.  Bob publishes the predictions as an Ocean asset

Put into csv form, and publish.


## 5.  Bob gives competition organizers access to the predictions

How: Send 1.0 datatokens to the competition organizers’ address