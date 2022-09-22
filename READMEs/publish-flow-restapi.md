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

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python. Includes: Config, Alice's wallet, Bob's wallet

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
asset = ocean.assets.create_url_asset(name, url, alice_wallet)
print(f"Just published asset, with did={asset.did}")
```

### 3. Alice makes the API asset available for free, via a dispenser

In the same Python console:
```python
from ocean_lib.models.datatoken import Datatoken
datatoken = Datatoken(ocean.web3, datatoken_address)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
datatoken.create_dispenser(
    dispenser_address=ocean.dispenser.address,
    max_balance=ocean.to_wei(10000),
    max_tokens=ocean.to_wei(10000),
    with_mint=True,
    allowed_swapper=ZERO_ADDRESS,
    from_wallet=alice_wallet,
)
dispenser_status = ocean.dispenser.status(datatoken.address)
assert dispenser_status[0:3] == [True, alice_wallet.address, True]
```

### 4.  Bob consumes the API asset

Now, you're Bob. All you have is the did of the data asset; you compute the rest.

In the same Python console:
```python
# Set asset did. Practically, you'd get this from Ocean Market. _This_ example uses prior info.
asset_did = asset.did

# Retrieve the Asset and datatoken objects
asset = ocean.assets.resolve(asset_did)
datatoken_address = asset.datatokens[0]["address"]
print(f"Asset retrieved, with did={asset.did}, and datatoken_address={datatoken_address}")

# Bob gets an access token from the dispenser
amt_dispense = 1
datatoken = Datatoken(ocean.web3, datatoken_address)
ocean.dispenser.dispense_tokens(
    datatoken=datatoken, amount=ocean.to_wei(amt_dispense), consumer_wallet=bob_wallet
)
bal = ocean.from_wei(datatoken.balanceOf(bob_wallet.address))
print(f"Bob now holds {bal} access tokens for the data asset.")

# Bob sends 1.0 datatokens to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(asset, bob_wallet)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access. He downloads the asset.
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
file_name = glob.glob(file_path + "/*")[0]
print(f"file_path: '{file_path}'")  # e.g. datafile.0xAf07...48,0
print(f"file_name: '{file_name}'")  # e.g. datafile.0xAf07...48,0/klines?symbol=ETHUSDT?int..22300

#verify that file exists
import os
assert os.path.exists(file_name), "couldn't find file"

# The file's data follows the Binance docs specs for Kline/Candlestick Data
# https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

#load from file into memory
with open(file_name, "r") as file:
    #data_str is a string holding a list of lists '[[1663113600000,"1574.40000000", ..]]'
    data_str = file.read().rstrip().replace('"', '')

#data is a list of lists
# -Outer list has one 7 entries; one entry per day.
# -Inner lists have 12 entries each: Kline open time, Open price, High price, Low price, close Price, Vol, ..
data = eval(data_str) 

#get close prices. These can serve as an approximation to spot price
close_prices = [float(data_at_day[4]) for data_at_day in data]

#or, we can put all data into a 2D array, to ease numerical processing
import numpy
D = numpy.asarray(data)
print(D.shape)
# returns:
# (7,12) #7 days, 12 entries per day
```








