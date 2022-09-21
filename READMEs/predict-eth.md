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

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python. Includes: Config, Alice's wallet, Bob's wallet

In this flow, Bob is a participant in the competition

## 2.  Get data locally from assets on Ocean

### 2.1  Get recent historical data from Binance ETH APIs

From [publish-flow-restapi](READMEs/publish-flow-restapi.md), do:
- [x] Bob consumes the API asset

###  2.2  Get other data

You can retrieve other data as you wish for the competition. However a key rule is that all data used in the competition must be published as assets on Ocean. If the data you're using isn't on Ocean yet, simply publish it there, then use it here.

Ocean Protocol Foundation (OPF) may make more data available as the competition proceeds.

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

You can put it online however you wish. Here are two possible ways:

- **GDrive.** First, navigate to the GFolder in GDrive you wish to upload the file to. Then, right click anywhere and select "File Upload". Once the csv is uploaded, right click on the file, and select "Share". In the popup, ensure that "General Access" is set to "Anyone with the link". Also in the popup, click "Copy link". That's your csv url. It should look something like `https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing`
- **GitHub.** First, create a new GitHub repo. Then, click on "add file", upload the file. Once uploaded, click on the file itself, then on "raw" button. The browser url is your csv url. It should look something like `https://raw.githubusercontent.com/<username>/<reponame>/main/predictions.csv`.


### 4.3 Publish (the csv) as an Ocean asset

In the same Python console:
```python
# Specify metadata
date_created = "2022-09-20T10:55:11Z"
name = "ETH predictions"
metadata = {
    "author": "<your name>", "name": name, "description": name,  "type": "dataset",
    "created": date_created, "updated": date_created, "license": "CC0: PublicDomain",
}

# Set the url, create UrlFile object
url="<your csv url>" #e.g. https://drive.google.com/file/d/1XU2NSKnN_epN71nwm5iKrN1t6-qGFbBJ/view?usp=sharing
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(url)

# Publish dataset. It creates the data NFT, datatoken, and fills in metadata
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
asset = ocean.assets.create(
    metadata,
    bob_wallet,
    [url_file],
    datatoken_templates=[1],
    datatoken_names=["Datatoken 1"],
    datatoken_symbols=["DT1"],
    datatoken_minters=[bob_wallet.address],
    datatoken_fee_managers=[bob_wallet.address],
    datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
    datatoken_publish_market_order_fee_tokens=[ocean.OCEAN_address],
    datatoken_publish_market_order_fee_amounts=[0],
    datatoken_bytess=[[b""]],
)
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
