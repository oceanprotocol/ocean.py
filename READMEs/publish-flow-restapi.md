<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for REST API-style URIs

This quickstart describes a flow to publish Kraken REST API of OCEAN-USD pair price feed, to make it available as free data asset on Ocean, and to consume it.

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
name = "Kraken API OCEAN-USD price feed"

url = "https://api.kraken.com/0/public/Ticker?pair=OCEANUSD"

#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": alice})
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
order_tx_id = ocean.assets.pay_for_access_service(ddo, {"from": bob})
asset_dir = ocean.assets.download_asset(ddo, bob, './', order_tx_id)

import os
file_name = os.path.join(asset_dir, 'file0')
```

Now, load the file and use its data.

The data follows the Kraken docs specs for Data, [here](https://docs.kraken.com/rest/#tag/Market-Data/operation/getTickerInformation).

In the same Python console:
```python

#load from file into memory
with open(file_name, "r") as file:
    #data is a string with the result inside.
    data_str = file.read().rstrip().replace("'", '"')

import json
data = json.loads(data_str)

#data is a list of lists
# -Outer dictionary contains 2 keys, one for errors and one for the result with the pair.
# -Inner dictionary have 9 entries each: Kline open time, Open price, High price, Low price, close Price, Vol, ..
#get close price
close_price = float(data['result']['OCEANUSD']['c'][0])
print(f"last close price: {close_price}")
```

