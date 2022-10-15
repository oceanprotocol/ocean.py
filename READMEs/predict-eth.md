<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It is used for Ocean Data Bounties competition.

During the competition, as we get feedback, we expect to continually evolve this README to make usage smooth.

Here are the steps:

1. Basic Setup
2. Get data locally. E.g. Binance ETH price feed
3. Make predictions
4. Publish predictions online, to private url
5. Share predictions test, via Ganache
6. Share predictions actual, to judges via Polygon

## 1. Setup

### 1.1 Prerequisites & installation

Prerequisites:
- Linux/MacOS
- Python 3.8.5+
- [Arweave Bundlr](https://docs.bundlr.network/docs/about/introduction): `npm install -g @bundlr-network/client` 

Now, let's install Python libraries. Open a terminal and:
```console
# Initialize virtual environment and activate it.
python3 -m venv venv
source venv/bin/activate

# Avoid errors for the step that follows
pip3 install wheel

# Install Ocean library
pip3 install ocean-lib

# Install pybundlr library
pip3 install pybundlr
```

### 1.2 Create Polygon Account (One-Time)

You'll be using Polygon network. So, please ensure that you have a Polygon account that holds some MATIC (at least a few $ worth). [More info](https://polygon.technology/matic-token/). 

### 1.3 Set envvars, for Polygon address

In the console:
```console
export REMOTE_TEST_PRIVATE_KEY1=<your Polygon private key>
```

### 1.4 Setup in Python, for Polygon

In the terminal, run Python: `python`

In the Python console:
```python
# Create Ocean instance
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config("https://polygon-rpc.com") # points to Polygon mainnet
config["BLOCK_CONFIRMATIONS"] = 1 #faster
ocean = Ocean(config)

# Create Alice's wallet (you're Alice)
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config["BLOCK_CONFIRMATIONS"], config["TRANSACTION_TIMEOUT"])
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "Alice needs MATIC"
```

## 2. Get data locally

Here, we grab Binance ETH/USDT price feed, which is published through Ocean as a free asset. You can see it on Ocean Market [here](https://market.oceanprotocol.com/asset/did:op:0dac5eb4965fb2b485181671adbf3a23b0133abf71d2775eda8043e8efc92d19).

In the same Python console:

```python
# Download file
asset_did = "did:op:0dac5eb4965fb2b485181671adbf3a23b0133abf71d2775eda8043e8efc92d19"
file_name = ocean.assets.download_file(asset_did, alice_wallet)

# Load file
with open(file_name, "r") as file:
    data_str = file.read().rstrip().replace('"', '')

data = eval(data_str)

#data is a list of lists
# -Outer list has entries at different times. 
# -Each inner list has 5 entries: timestamp, Open price, High price, Low price, Close price
# -It looks like: [[1662998400000,1706.38,1717.87,1693,1713.56],[1663002000000,1713.56,1729.84,1703.21,1729.08],[1663005600000,1729.08,1733.76,1718.09,1728.83],...

#Example: get close prices. These can serve as an approximation to spot price
close_prices = [float(data_at_day[4]) for data_at_day in data]
```


## 3.  Make predictions

### 3.1  Build a simple AI model

Here's where you build whatever AI/ML model you want, leveraging the data from the previous step.

This demo flow skips building a model because the next step will simply generate random predictions.

### 3.2  Run the AI model to make future ETH price predictions

Predictions must be one prediction every hour on the hour, for a 24h period: Oct 3 at 1:00am UTC, at 2:00am, at 3:00am, ..., 11.00pm, 12.00am. Therefore there are 24 predictions total.

In the same Python console:
```python
import random
pred_vals = [1500.0 - 100.0 + 200.0 * random.random() for i in range(24)] 
```

## 4.  Publish predictions online, to private url

### 4.1 Save the predictions as a csv file

In the same Python console:
```python
from pathlib import Path
file_name = "/tmp/pred_vals.csv"
p = Path(file_name)
p.write_text(str(pred_vals))
```

The csv will look something like:

```text
1503.134,1512.490,1498.982,...,1590.673
```

### 4.2 Put the csv online

Here, we upload to Arweave permanent decentralized file storage, via Bundlr. This makes the predictions tamper-proof.

In the same Python console:
```python
from pybundlr import pybundlr
file_name = "/tmp/pred_vals.csv"
url = pybundlr.fund_and_upload(file_name, "matic", alice_wallet.private_key)
print(f"Your csv url: {url}")
```

Your url is only open to those who know it. Below, we'll only share to the judges.


## 5. Share predictions test, via Ganache

In this section, we'll do a dry run of sharing the predictions with local Ganache testnet, and also show how the predictions are evaluated.

First, to minimize chance of crossed wires: exit your Python console.

### 5.1 Setup on Ganache

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Download barge and run services
- [x] Setup : Set envvars (for Ganache addresses)
- [x] Setup : Setup in Python

In this flow, Alice is you -- the participant in the competition.

### 5.2 Publish the csv as an Ocean asset

In the same Python console:
```python
url = "<your csv url>" 
#e.g. url = "https://arweave.net/qctEbPb3CjvU8LmV3G_mynX74eCxo1domFQIlOBH1xU"
name = "ETH predictions"
(data_nft, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet)
print(f"New asset created, with did={asset.did}, and datatoken.address={datatoken.address}")
```

### 5.3 Share predictions to Bob

In the same Python console:
```python
to_address = bob_wallet.address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
```

### 5.4 Analyze results: retrieve predictions

This step and the next simulate what the judges ("Bob" here) will do with the predictions you shared: retrieve them, then calculate NMSE. You can use it to see how your predictions will be scored.

```python
# Download file
file_name = ocean.assets.download_file(asset.did, bob_wallet)

# Load file
from pathlib import Path
p = Path(file_name)
s = p.read_text()
pred_vals = eval(s)
print(f"Bob retrieved the file, it has {len(pred_vals)} predictions")
```

### 5.5 Analyze results: calculate NMSE

In the same Python console:

```python
#set target_unixtimes
from datetime import datetime, timedelta
import time
start_datetime = datetime(2022, 10, 17, 1, 00) #Oct 17, 2022 at 1:00am
target_datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]
assert len(pred_vals) == len(target_datetimes), "wrong # predictions"

def _unixtime(datetime):
    return time.mktime(datetime.timetuple())
    

import numpy as np
target_unixtimes = np.asarray([_unixtime(datetime) for datetime in target_datetimes])

#get the most recent day of *true* ETH price data
# Warning: This assumes that your predictions are also the most recent day. If they don't line up, errors will be high.

import requests
result = requests.get("https://cexa.oceanprotocol.io/ohlc?exchange=binance&pair=ETH/USDT&period=1d")
allcex_x = result.json() #list with 500 entries. Each data[i] is a list with 6 entries
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

## 6. Share predictions actual, to judges via Polygon

Only do these steps once you're satisfied enough to submit the results. You'll be operating on a remote network (Polygon) rather than the previous local one (Ganache).

First, to minimize chance of crossed wires: exit your Python console, and ctrl-c barge running in its console.

### 6.1 Setup on Polygon

From section 1 of this console, do:
- [x] Setup: set envvars, for Polygon address
- [x] Setup in Python, for Polygon

### 6.2 Publish the csv as an Ocean asset, in Polygon

(This is identical to section 5, except now it's on Polygon not Ganache)

In the same Python console:
```python
url = "<your csv url>" 
#e.g. url = "https://arweave.net/qctEbPb3CjvU8LmV3G_mynX74eCxo1domFQIlOBH1xU"
name = "ETH predictions"
(data_nft, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet, wait_for_aqua=False)
print(f"New asset created, with did={asset.did}, and datatoken.address={datatoken.address}")
```

Write down the `did` and `datatoken_address`. You'll be needing to share it in the Questbook entry.

### 6.2 Share predictions to judges, in Polygon

In the same Python console:
```python
to_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E" #official judges address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
```

Finally, ensure you've filled in your Questbook entry.

Now, you're complete! Thanks for being part of this competition.
