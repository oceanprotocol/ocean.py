<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It used for Ocean Data Bounties competition.

During the competition, as we get feedback, we expect to continually evolve this README to make usage smooth.

Here are the steps:

1. Basic Setup
2. Get data locally. E.g. Binance ETH price feed
3. Make predictions
4. Publish predictions online, to private url
5. Share predictions test, via Ganache
6. Share predictions actual, to organizers via Mumbai

## 1. Basic Setup

### Prerequisites & installation

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Installation 2: Specific for this README

The [ccxt](https://github.com/ccxt/ccxt) library has a unified interface to many crypto exchanges. We'll be using it. 

In console:
```
pip install ccxt
```


## 2.  Get data locally. E.g. Binance ETH price feed

ccxt offers public APIs, so we use those directly. (No need for using Ocean for this case.)

In Python console:

```python
import ccxt
import numpy as np

#get the most recent week of ETH price data: Open, High, Low, Close, Volume (OHLCV)
x = ccxt.binance().fetch_ohlcv('ETH/USDT', '1w')

print(x)
# gives a list of lists. Outer list has 268 entries. Inner list has 6 entries: unix timestamp, O, H, L, C, V
# [[1502668800000, 301.13, 312.18, 278.0, 299.1, 21224.89324], [1503273600000, 299.1, 348.13, 144.21, 348.13, 45233.88589], ...]
```


## 3.  Make predictions

### 3.1  Build a simple AI model

Here's where you build whatever AI/ML model you want, leveraging the data from the previous step.

This demo flow skips building a model because the next step will simply generate random predictions.

### 3.2  Run the AI model to make future ETH price predictions

Predictions must be one prediction every hour on the hour, for a 24h period: from Oct 3, 2022 at 1:00am UTC, to Oct 4, 2022 at 1:00am UTC.

In the same Python console:
```python
from datetime import datetime, timedelta
start_datetime = datetime(2022, 10, 17, 1, 00) #Oct 17, 2022 at 1:00am
datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]

#make predictions. Typically you'd use the AI model. For simplicity for now, we make random predictions
import random
pred_vals = [1500.0 - 100.0 + 200.0 * random.random() for i in range(len(datetimes))] 
```


## 4. Put predictions online, to private url

### 4.1 Save the predictions as a csv file

In the same Python console:
```python
import csv
with open("/tmp/pred_vals.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(pred_vals)
```

The csv will look something like this:

```text
1503.134,1512.490,1498.982,...,1590.673
```

### 4.2 Put the csv online

You can put it online however you wish. Here's one way, with Google Drive.

1. First, navigate to the GFolder in GDrive you wish to upload the file to.
2. Then, right click anywhere and select "File Upload".
3. Once the csv is uploaded, right click on the file, and select "Share".
4. In the popup, ensure that "General Access" is set to "Anyone with the link".
5. Also in the popup, click "Copy link". That's your csv url. It should look something like `https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing`

Your csv url is only open to those who know it. So we only share to selected parties (the organizers).


## 5. Share predictions test, via Ganache

In this section, we'll do a dry run of sharing the predictions with local Ganache testnet, and also show how the predictions are evaluated.

### 5.1 Setup on Ganache

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars
- [x] Setup : Setup in Python. Includes: Config, Alice's wallet, Bob's wallet

In this flow, Alice is you -- the participant in the competition.


### 5.2 Publish the csv as an Ocean asset

In the same Python console:
```python
url="<your csv url>" 
#e.g. url="https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing"
name = "ETH predictions"
asset = ocean.assets.create_url_asset(name, url, alice_wallet)

datatoken_address = asset.datatokens[0]["address"]
print(f"New asset created, with did={asset.did}, and datatoken_address={datatoken_address}")
```

### 5.3 Share predictions to Bob

In the same Python console:
```python
#retrieve Datatoken object
from ocean_lib.models.datatoken import Datatoken
datatoken = Datatoken(ocean.web3, datatoken_address)

#send tokens to Bob
to_address=bob_wallet.address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
```

### 5.4 Analyze results: retrieve predictions

This step and the next simulate what organizers ("Bob" here) will do with the predictions you shared: retrieve them, then calculate NMSE. You can use it to see how your predictions will be scored.

```python
# Bob sends 1.0 datatokens to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(asset, bob_wallet)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access. He downloads the asset.
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset, consumer_wallet=bob_wallet, destination='./', order_tx_id=order_tx_id)
import glob
file_name = glob.glob(file_path + "/*")[0]
print(f"file_path: '{file_path}'")  # e.g. datafile.0xAf07...48,0
print(f"file_name: '{file_name}'")  # e.g. datafile.0xAf07...48,0/klines?symbol=ETHUSDT?int..22300

#verify that file exists
import os
assert os.path.exists(file_name), "couldn't find file"

import csv
import numpy as np
with open(file_name, "r") as f:
    for row in csv.reader(f):
    	pred_vals = row; break
pred_vals = np.asarray([float(p) for p in pred_vals])
print(f"Bob retrieved the file, it has {len(pred_vals)} predictions")
```

### 5.5 Analyze results: calculate NMSE


```python
#set target_unixtimes
import time
from datetime import datetime, timedelta
start_datetime = datetime(2022, 10, 17, 1, 00) #Oct 17, 2022 at 1:00am
target_datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]
assert len(pred_vals) == len(target_datetimes), "wrong # predictions"

def _unixtime(datetime):
    return time.mktime(datetime.timetuple())
    
target_unixtimes = np.asarray([_unixtime(datetime) for datetime in target_datetimes])

#get the most recent day of ETH price data
import ccxt
allcex_x = ccxt.binance().fetch_ohlcv('ETH/USDT', '1d')
allcex_unixtimes = np.asarray([inner[0] for inner in allcex_x])
allcex_vals = np.asarray([inner[4] for inner in allcex_x])

#cex_vals = only at the timestamps that line up with those of predictions
cex_vals = np.zeros(len(target_unixtimes))
for i, target_unixtime in enumerate(target_unixtimes):
    time_diffs = np.abs(allcex_unixtimes - target_unixtime)
    j = np.argmin(time_diffs)
    cex_vals[i] = allcex_vals[j]

#calculate NMSE
mse_xy = np.sum(np.square(cex_vals - pred_vals))
mse_x = np.sum(np.square(cex_vals))
nmse = mse_xy / mse_x
print(f"NMSE = {nmse}")
```

## 6. Share predictions actual, to organizers via Mumbai

Only do these steps once you're satisfied enough to submit the results. You'll be operating on a remote network (Mumbai) rather than the previous local one (Ganache).

First, to ensure they don't cross wires: ctrl-c out of (a) Python console and (b) barge running in a different console.

### 6.1 Setup on Mumbai

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python. Includes: Config, Alice's wallet, Bob's wallet

### 6.2 Publish the csv as an Ocean asset, in Mumbai

(This is identical to before, except now it's on Mumbai not Ganache)

In the same Python console:
```python
url="<your csv url>" 
#e.g. url="https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing"
name = "ETH predictions"
asset = ocean.assets.create_url_asset(name, url, alice_wallet)

datatoken_address = asset.datatokens[0]["address"]
print(f"New asset created, with did={asset.did}, and datatoken_address={datatoken_address}")
```

Write this down, as you will want to share this

### 6.2 Share predictions to organizers, in Polygon

In the same Python console:
```python
#retrieve Datatoken object
from ocean_lib.models.datatoken import Datatoken
datatoken = Datatoken(ocean.web3, datatoken_address)

#send tokens to organizer
to_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E" #official organizer address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
```
