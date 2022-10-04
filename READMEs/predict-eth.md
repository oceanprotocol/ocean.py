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

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### 1.2 Create Polygon Account (One-Time)

You'll be using Polygon to retrieve Ocean data assets, and publish your ETH predictions. So, you will need a Polygon account with a small amount of MATIC to pay for gas. If you have an account already (and its private key), you can skip this section.

In your console, run Python.
```console
python
```

In the Python console:
```python
from eth_account.account import Account
account1 = Account.create()
print(f"""
export REMOTE_TEST_PRIVATE_KEY1={account1.key.hex()}
export ADDRESS1={account1.address}
""")
```

Then, hit Ctrl-C to exit the Python console.

Now, you have a Polygon account: a private key with associated address. It actually works on any chain, not just Polygon. Save the private key somewhere safe, like a local file or a password manager. 

Then, get some MATIC into that account, on the Polygon network. [Here's](https://polygon.technology/matic-token/) a starting point. A few $ worth is more than enough to pay for transactions of this README.

### 1.3 Set envvars

In the console:
```console
# For accounts: set private keys
export REMOTE_TEST_PRIVATE_KEY1=<your REMOTE_TEST_PRIVATE_KEY1>
```

### 1.4 Setup in Python, for Polygon

Let's load services info and account info into Python `config` dict and `Wallet` objects respectively.

In your working console, run Python:

```console
python
```

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
# Retrieve the Asset and datatoken objects
from ocean_lib.models.datatoken import Datatoken
asset_did = "did:op:0dac5eb4965fb2b485181671adbf3a23b0133abf71d2775eda8043e8efc92d19"
asset = ocean.assets.resolve(asset_did)
datatoken_address = asset.datatokens[0]["address"]
datatoken = Datatoken(ocean.web3, datatoken_address)
print(f"Asset retrieved, with did={asset.did}, and datatoken_address={datatoken_address}")

# Alice gets a datatoken from the dispenser
amt_dispense_wei = ocean.to_wei(1)
ocean.dispenser.dispense_tokens(datatoken, amt_dispense_wei, consumer_wallet=alice_wallet)
bal = ocean.from_wei(datatoken.balanceOf(alice_wallet.address))
print(f"Alice now holds {bal} datatokens to access the data asset.")

# Alice sends datatoken to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(asset, alice_wallet)
print(f"order_tx_id = '{order_tx_id}'")

# Alice now has access. She downloads the asset.
# If the connection breaks, Alice can request again by showing order_tx_id.
# If you still encounter issues, the Appendix has a workaround.
file_path = ocean.assets.download_asset(
    asset, consumer_wallet=alice_wallet, destination='./', order_tx_id=order_tx_id)

# Get file_name
import glob
file_name = glob.glob(file_path + "/*")[0]
print(f"file_name: '{file_name}'")  # e.g. datafile.0xAf07...48,0/klines?symbol=ETHUSDT?int..22300

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
import csv
with open("/tmp/pred_vals.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(pred_vals)
```

The csv will look something like:

```text
1503.134,1512.490,1498.982,...,1590.673
```


### 4.2 Put the csv online

You can put it online however you wish. Here's one way, with Google Drive.

1. First, navigate to the GFolder in GDrive you wish to upload the file to.
2. Then, right click anywhere and select "File Upload".
3. Once the csv is uploaded, right click on the file, and select "Share".
4. In the popup, ensure that "General Access" is set to "Anyone with the link".
5. Also in the popup, click "Copy link". It should look something like `https://drive.google.com/file/d/1uZakKrzkSYosD_wf-EFJusFhzlOGQRRy/view?usp=sharing`. Then, in the popup, click "Done".
6. If you paste the copied link into the browser, it will load an HTML page. But we don't want an html url, we want a  _downloadable_ one. Here's how. 
   - First, note the `<FILE-ID>` from the previous step (e.g. "1uZ..RRy").
   - Then, create a URL according to: `https://drive.google.com/uc?export=download&id=<FILE-ID>`. **This is your url.** 
   - In our running example, the url is `https://drive.google.com/uc?export=download&id=1uZakKrzkSYosD_wf-EFJusFhzlOGQRRy`

Your csv url is only open to those who know it. So we only share to selected parties (the judges).


## 5. Share predictions test, via Ganache

In this section, we'll do a dry run of sharing the predictions with local Ganache testnet, and also show how the predictions are evaluated.

### 5.1 Setup on Ganache

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Download barge and run services
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

In this flow, Alice is you -- the participant in the competition.

"Setup in Python" set up Alice's wallet. Let's set up Bob's wallet too. In the same Python console:

```python
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config["BLOCK_CONFIRMATIONS"], config["TRANSACTION_TIMEOUT"])
print(f"bob_wallet.address = '{bob_wallet.address}'")
```

### 5.2 Publish the csv as an Ocean asset

In the same Python console:
```python
url="<your csv url>" 
#e.g. url="https://drive.google.com/uc?export=download&id=1uZakKrzkSYosD_wf-EFJusFhzlOGQRRy"
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

This step and the next simulate what the judges ("Bob" here) will do with the predictions you shared: retrieve them, then calculate NMSE. You can use it to see how your predictions will be scored.

```python
# Bob sends 1.0 datatokens to the service, to get access
order_tx_id = ocean.assets.pay_for_access_service(asset, bob_wallet)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access. He downloads the asset.
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset, consumer_wallet=bob_wallet, destination='./', order_tx_id=order_tx_id)
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

# If you encountered issues going through this, a workaround is to get pred_vals directly from your AI model.
```

### 5.5 Analyze results: calculate NMSE

```python
#set target_unixtimes
from datetime import datetime, timedelta
import numpy as np
import time
start_datetime = datetime(2022, 10, 17, 1, 00) #Oct 17, 2022 at 1:00am
target_datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]
assert len(pred_vals) == len(target_datetimes), "wrong # predictions"

def _unixtime(datetime):
    return time.mktime(datetime.timetuple())
    
target_unixtimes = np.asarray([_unixtime(datetime) for datetime in target_datetimes])

#get the most recent day of *true* ETH price data
# Warning: This assumes that your predictions are also the most recent day. If they don't line up, errors will be high.
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

## 6. Share predictions actual, to judges via Polygon

Only do these steps once you're satisfied enough to submit the results. You'll be operating on a remote network (Polygon) rather than the previous local one (Ganache).

First, to ensure they don't cross wires: ctrl-c out of (a) Python console and (b) barge running in a different console.

### 6.1 Setup on Polygon

From section 1 of this console, do:
- [x] Setup: set envvars
- [x] Setup in Python, for Polygon

### 6.2 Publish the csv as an Ocean asset, in Polygon

(This is identical to section 5, except now it's on Polygon not Ganache)

In the same Python console:
```python
url="<your csv url>" 
#e.g. url="https://drive.google.com/uc?export=download&id=1uZakKrzkSYosD_wf-EFJusFhzlOGQRRy"
name = "ETH predictions"
asset = ocean.assets.create_url_asset(name, url, alice_wallet) #this will take 30-60 seconds, be patient
datatoken_address = asset.datatokens[0]["address"]
print(f"New asset created, with did={asset.did}, and datatoken_address={datatoken_address}")
```

Write down the `did` and `datatoken_address`. You'll be needing to share it in the Questbook entry.

### 6.2 Share predictions to judges, in Polygon

In the same Python console:
```python
#retrieve Datatoken object
from ocean_lib.models.datatoken import Datatoken
datatoken = Datatoken(ocean.web3, datatoken_address)

#send tokens to judges
to_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E" #official judges address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
```

Finally, ensure you've filled in your Questbook entry.

Now, you're complete! Thanks for being part of this competition.

## Appendix: Workaround

This is the first round of the predict-ETH competitions. It supplies just one Ocean data asset, a simple ETH/USDT price feed from Binance. Future rounds will have more assets, from more sources both on-chain and off.

But since this is the first round with just one simple asset: if you encounter issues in accessing it, there's a workaround. You can proceed by using the URL directly: https://cexa.oceanprotocol.io/ohlc?exchange=binance&pair=ETH/USDT

Here's how to do it in Python:

```python
import requests
import numpy as np
result = requests.get("https://cexa.oceanprotocol.io/ohlc?exchange=binance&pair=ETH/USDT")
data = result.json() #list with 500 entries. Each x[i] is a list with 6 entries
```
