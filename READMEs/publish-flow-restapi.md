<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for REST API-style URIs

This quickstart describes a flow to publish Binance REST API of ETH price feed, to make it available as free data asset on Ocean, and to consume it.

Here are the steps:

1.  Setup
2.  Alice publishes the API asset
3.  Alice makes the API asset available for free, via a dispenser
4.  Bob consumes the API asset

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
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice_wallet)
print(f"Just published asset, with did={ddo.did}")
```

### 3. Alice makes the API asset available for free, via a dispenser

In the same Python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from web3.main import Web3
datatoken.createDispenser(
    ocean.dispenser.address,
    Web3.toWei(10000, "ether"),
    Web3.toWei(10000, "ether"),
    True,
    ZERO_ADDRESS,
    {"from": alice_wallet},
)
dispenser_status = ocean.dispenser.status(datatoken.address)
assert dispenser_status[0:3] == [True, alice_wallet.address, True]
```

### 4. Bob consumes the API asset

Now, you're Bob. First, download the file.

In the same Python console:
```python
# Set asset did. Practically, you'd get this from Ocean Market. _This_ example uses prior info.
ddo_did = ddo.did

# Bob gets a datatoken from the dispenser; sends it to the service; downloads
file_name = ocean.assets.download_file(ddo_did, bob_wallet)
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
# Bob gets an access token from the dispenser
ddo = ocean.assets.resolve(ddo_did)
datatoken_address = ddo.datatokens[0]["address"]
datatoken = ocean.get_datatoken(datatoken_address)
amt_tokens = Web3.toWei(1, "ether")
ocean.dispenser.dispense_tokens(datatoken, amt_tokens, {"from": bob_wallet})

# Bob sends a datatoken to the service to get access
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob_wallet)

# Bob downloads the dataset
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=ddo,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
import glob
file_name = glob.glob(file_path + "/*")[0]
print(f"file_name: '{file_name}'")
```








