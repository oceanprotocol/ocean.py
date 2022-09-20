<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It runs on Mumbai.

Here are the steps:

1.  Setup
2.  Get data locally from assets on Ocean
  2.1  Get Binance API of historical ETH price
  2.2  CSV with many years of past ETH price
3.  Make predictions :
  3.1  Build a simple AI model (client-side)
  3.2  Run the AI model to make future ETH price predictions
4.  Publish the predictions as an Ocean asset
5.  Give competition organizers access to the predictions

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
- (We do _not_ set up Alice's wallet, since we're Bob int this this flow.)

From [c2d-flow](c2d-flow.md), do:
- [x] Setup Bob's Wallet

## 2.  Get data locally from assets on Ocean

### 2.1 Get Binance API of historical ETH price

In the same Python console:
```python
amt_dispense = 1
ocean.dispenser.dispense_tokens(
    datatoken=datatoken, amount=ocean.to_wei(amt_dispense), consumer_wallet=bob_wallet
)
bal = ocean.from_wei(datatoken.balanceOf(bob_wallet.address))
print(f"Bob just got a datatoken to access to Binance API of ETH price. He holds {bal} tokens.")
```

###  2.2  CSV with many years of past ETH price

## 3.  Make predictions :

### 3.1  Build a simple AI model (client-side)

### 3.2  Run the AI model to make future ETH price predictions

Predictions are for a near-future 24h period, one prediction every hour on the hour.

## 4.  Publish the predictions as an Ocean asset

Put into csv form, and publish.


## 5.  Give competition organizers access to the predictions

How: Send 1.0 datatokens to the competition organizers’ address