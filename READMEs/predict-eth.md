<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It used for Ocean Data Bounties competition.

The text below uses Mumbai. We recommend starting with this for testing. Then when you're ready to move to submit your result, switch to Polygon and go through the flow again.

During the competition, as we get feedback, we expect to continually evolve this README to make usage smooth.

Here are the steps:

1. Setup
2. Get data locally from assets on Ocean
   - Get recent historical data from Binance ETH API
   - Get other data
3. Make predictions
   - Build a simple AI model
   - Run the AI model to make future ETH price predictions
4. Publish the predictions as an Ocean asset
   - Save the predictions as a csv file
   - Put the csv online
   - Publish as an Ocean asset
5.  Share csv access to the competition organizers

## 1. Setup

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

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python. Includes: Config, Alice's wallet, Bob's wallet

In this flow, Bob is a participant in the competition

## 2.  Get data locally

ccxt offers public APIs, so we use those directly. (No need for having Ocean in the loop, for this case.)

In Python console:

```python
import ccxt
import numpy as np

#get the most recent week of ETH data: Open, High, Low, Close, Volume (OHLCV)
x = ccxt.binance().fetch_ohlcv(ETH/USDT', '1w')

print(x)
# gives a list of lists. Outer list has 268 entries. Inner list has 6 entries: unix timestamp, O, H, L, C, V
# [[1502668800000, 301.13, 312.18, 278.0, 299.1, 21224.89324], [1503273600000, 299.1, 348.13, 144.21, 348.13, 45233.88589], [1503878400000, 348.11, 394.39, 320.08, 341.77, 33886.41427], ...]
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
start_datetime = datetime(2022, 10, 3, 1, 00) #Oct 3, 2022 at 1:00am
datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]

#make predictions. Typically you'd use the AI model. For simplicity for now, we make random predictions
import random
predictions = [1500.0 - 100.0 + 200.0 * random.random() for i in range(len(datetimes))] 
```

## 4.  Publish the predictions as an Ocean asset

### 4.1 Save the predictions as a csv file

In the same Python console:
```python
filename = "/tmp/predictions.csv"
with open(filename, "w") as file:
    file.write("Datetime, predicted-ETH-value\n")
    for datetime_, prediction in zip(datetimes, predictions):
        file.write(f"{datetime_.strftime('%Y-%m-%d::%H:%M')}, {prediction:.3f}\n")
```

The csv will look something like this:

```text
Datetime, predicted-ETH-value
2022-10-03::01:00, 1503.134
2022-10-03::02:00, 1512.490
2022-10-03::03:00, 1498.982
...
2022-10-03::11:00, 1578.301
2022-10-04::00:00, 1582.429
2022-10-04::01:00, 1590.673
```

### 4.2 Put the csv online

You can put it online however you wish. Here's one way, with Google Drive.

1. First, navigate to the GFolder in GDrive you wish to upload the file to.
2. Then, right click anywhere and select "File Upload".
3. Once the csv is uploaded, right click on the file, and select "Share".
4. In the popup, ensure that "General Access" is set to "Anyone with the link".
5. Also in the popup, click "Copy link". That's your csv url. It should look something like `https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing`

Now you have a publicly accessible url, that is nonetheless hard for others to discover. Let's publish it as an Ocean asset.


### 4.3 Publish (the csv) as an Ocean asset

In the same Python console:
```python
# Specify metadata
date_created = "2022-09-20T10:55:11Z"
name = "ETH predictions by <your name>"
url="<your csv url>" #e.g. https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing

# Create asset
asset = ocean.assets.create_url_asset(name, url, bob_wallet)

datatoken_address = asset.datatokens[0]["address"]
print(f"New asset created, with did={asset.did}, and datatoken_address={datatoken_address}")
```

Take note of the did; you'll need to include it when you enter the competition via Questbook.


## 5.  Share csv access to the competition organizers

Only do this step once you've gone through the rest, both for Mumbai (for testing), then for Polygon (for production). Only submissions on Polygon are accepted.

In the same Python console:
```python
#this is the official organizer address
organizer_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E"

#retrieve Datatoken object
from ocean_lib.models.datatoken import Datatoken
datatoken = Datatoken(ocean.web3, datatoken_address)

#mint tokens into the account. >1 to make it organizers to share amongst each other.
datatoken.mint(
    account_address=organizer_address,
    value=ocean.to_wei(10),
    from_wallet=bob_wallet,
)
```
