<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price, with the help of a local AI model. It runs on Mumbai.

Here are the steps:
0. Setup
1. Get data locally from these assets on Ocean:
  - Binance API price feed of ETH-USDT
  - CSV with many years of past ETH price
2. Make predictions :
  2.1 Build a simple ML model (client-side)
  2.2 Run the ML model to make future ETH price predictions. Predictions are for a near-future 24h period, one prediction every hour on the hour.
3. Publish the predictions as a csv, in a new Ocean asset
4. Send 1.0 datatokens to the competition organizers’ address

## o. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Alice Publishes API data asset