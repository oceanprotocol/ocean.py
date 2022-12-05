<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for REST API-style URIs

This quickstart describes a flow to publish Binance REST API of ETH price feed, to make it available as free data DDO on Ocean, and to consume it.

Here are the steps:

1.  Setup
2.  Alice publishes the API DDO
3.  Alice creates a faucet for the DDO
4.  Bob gets a free datatoken, then consumes it

Let's go through each step.

## 1. Setup

### Prerequisites & installation

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

## 2. Alice publishes the API DDO

In the same Python console:
```python
#data info
name = "Binance API v3 klines"

from datetime import datetime, timedelta
end_datetime = datetime.now()
start_datetime = end_datetime - timedelta(days=7) #the previous week
url = f"https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={int(start_datetime.timestamp())*1000}&endTime={int(end_datetime.timestamp())*1000}"

#create DDO
(data_nft, datatoken, ddo) = ocean.ddo.create_url_ddo(name, url, alice_wallet)
print(f"Just published DDO with did={ddo.did}")
```

### 3. Alice creates a faucet for the DDO

In the same Python console:
```python
datatoken.create_dispenser({"from": alice_wallet})
```

### 4. Bob gets a free datatoken, then consumes it

Now, you're Bob. First, download the file.

In the same Python console:
```python
# Set DDO did. Practically, you'd get this from Ocean Market. _This_ example uses prior info.
ddo_did = ddo.did

# Bob gets a free datatoken, sends it to the service, and downloads
file_name = ocean.ddo.download_file(ddo_did, bob_wallet)
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

## Appendix. Further Flexibility

Step 4's `download_file()` did three things:

- Checked if Bob has access tokens. He didn't, so the dispenser gave him some
- Sent a datatoken to the service to get access
- Downloaded the file

Here are the three steps, un-bundled.

In the same Python console:
```python
# Bob gets an access token from the faucet dispenser
ddo = ocean.ddo.resolve(ddo_did)
datatoken_address = ddo.datatokens[0]["address"]
datatoken = ocean.get_datatoken(datatoken_address)
datatoken.dispense("1 ether", {"from": bob_wallet})

# Bob sends a datatoken to the service to get access
order_tx_id = ocean.ddo.pay_for_access_service(ddo, bob_wallet)

# Bob downloads the dataset
# If the connection breaks, Bob can request again by showing order_tx_id.
consumer_wallet = bob_wallet
destination = './'
file_path = ocean.ddo.download_ddo(
    ddo, consumer_wallet, destination, order_tx_id
)
import glob
file_name = glob.glob(file_path + "/*")[0]
print(f"file_name: '{file_name}'")
```
