<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for REST API-style URIs

This quickstart describes a flow to publish Binance REST API of ETH price feed, to make it available as free data asset on Ocean, and to consume it.

Here are the steps:

1.  Setup
2.  Alice publishes the API asset
3.  Alice creates a faucet for the asset
4.  Bob gets a free datatoken, then consumes it

Let's go through each step.

## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

## 2. Alice publishes the API asset

In the same Python console:
```python
#data info
name = "Binance API v3 klines"

from datetime import datetime, timedelta
end_datetime = datetime.now()
start_datetime = end_datetime - timedelta(days=7) #the previous week
url = f"https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={int(start_datetime.timestamp())*1000}&endTime={int(end_datetime.timestamp())*1000}"

#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice)
print(f"Just published asset, with did={ddo.did}")
```

### 3. Alice creates a faucet for the asset

In the same Python console:
```python
datatoken.create_dispenser({"from": alice})
```

### 4. Bob gets a free datatoken, then consumes it

Now, you're Bob. First, download the file.

In the same Python console:
```python
# Set asset did. Practically, you'd get this from Ocean Market. _This_ example uses prior info.
ddo_did = ddo.did

# Bob gets a free datatoken, sends it to the service, and downloads
datatoken.dispense("1 ether", {"from": bob})
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob)
file_name = ocean.assets.download_asset(ddo, bob, './', order_tx_id)
```

Now, load the file and use its data.

The data follows the Binance docs specs for Kline/Candlestick Data, [here](https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data).

In the same Python console:
```python

#load from file into memory
with open(file_name, "r") as file:
    #data_str is a string holding a list of lists '[[1663113600000,"1574.40000000", ..]]'
    data_str = file.read().rstrip().replace('"', '')


data = eval(data_str)

#data is a list of lists
# -Outer list has one 7 entries; one entry per day.
# -Inner lists have 12 entries each: Kline open time, Open price, High price, Low price, close Price, Vol, ..

#get close prices
close_prices = [float(data_at_day[4]) for data_at_day in data]
```

