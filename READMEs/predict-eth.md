<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Predict Future ETH Price

This quickstart describes a flow to predict future ETH price via a local AI model. It used for Ocean Data Bounties competition. It runs on Polygon.

Here are the steps:

1.  Setup, for Mumbai
2.  Get data locally from assets on Ocean
  2.1  Get recent historical data from Binance ETH API
  2.2  Get older historical data from a CSV file
3.  Make predictions :
  3.1  Build a simple AI model
  3.2  Run the AI model to make future ETH price predictions
4.  Publish the predictions as an Ocean asset
  4.1 Save the predictions as a csv file
  4.2 Put the csv online
  4.3 Publish as an Ocean asset
5.  Share csv access to the competition organizers

## 1. Setup, for Mumbai

### Prerequisites & installation

From [simple-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

### Setup for remote

From [simple-remote](simple-remote.md), do:
- [x] Create Mumbai Accounts (One-Time)
- [x] Create Config File for Services
- [x] Set envvars
- [x] Setup in Python: Create Ocean instance

In this flow, Bob is the competitor. (And, we don't need to set up Alice's wallet.)

From [c2d-flow](c2d-flow.md), do:
- [x] Setup Bob's Wallet

## 2.  Get data locally from assets on Ocean

### 2.1  Get recent historical data from Binance ETH APIs

In the same Python console:
```python
# With did of Binance API asset, Bob retrieves the Asset, data_nft, and datatoken objects
asset_did = <copy and paste from where you have it. E.g. from Ocean Market or publish-asset.md>

asset = ocean.assets.resolve(asset_did)
data_nft = asset.nft
datatoken = asset.datatokens[0]

print(f"Asset retrieved, with name: {data_nft.token_name()}")
print(f"  did: {asset.did}")
print(f"  data_NFT.address: {data_nft.address}")
print(f"  datatoken.address: {datatoken.address}")

# Bob gets an access token from the dispenser
amt_dispense = 1
ocean.dispenser.dispense_tokens(
    datatoken=datatoken, amount=ocean.to_wei(amt_dispense), consumer_wallet=bob_wallet
)
bal = ocean.from_wei(datatoken.balanceOf(bob_wallet.address))
print(f"Bob now holds {bal} access tokens for the data asset.")


# Bob sends 1.0 datatokens to the service, to get access
service = asset.services[0] #retrieve service object
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken.address,
    consume_market_order_fee_amount=0,
    wallet=bob_wallet,
)
print(f"order_tx_id = '{order_tx_id}'")

# Bob now has access. He downloads the asset.
# If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    service=service,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
print(f"file_path = '{file_path}'")  # e.g. datafile.0xAf07...
```

The file downloaded is a .json. From that, use the python `json` library to parse it as desired.)

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```


###  2.2  Get older historical data from a CSV file

(FILLME later. Or skip)

## 3.  Make predictions

### 3.1  Build a simple AI model

(FILLME later. Use e.g. leverage gpr.py here: https://github.com/oceanprotocol/c2d-examples/blob/4182e8cfec043a5e7c946d18304dcae244581a6c/branin_and_gpr/gpr.py#L69)

### 3.2  Run the AI model to make future ETH price predictions

Predictions must be one prediction every hour on the hour, for a 24h period: from Oct 3, 2022 at 1:00am UTC, to Oct 4, 2022 at 1:00am UTC.

In the same Python console:
```python
from datetime import datetime, timedelta
start_datetime = datetime(st, 2022, 10, 03, 01, 00)
datetimes = [start_datetime + timedelta(hours=hours) for hours in range(24)]
predictions = [1500.0 + 100.0 * random.random() for i in range(len(datetimes))] #example predictions
```

## 4.  Publish the predictions as an Ocean asset

### 4.1 Save the predictions as a csv file

The csv has two columns: date/time, and predicted ETH value (in terms of USDT). The date/time values must fit the format below. Bob needs to make a prediction for each date/time.

| Datetime          | predicted-ETH-value |
| ----------------- | ------------------- |
| 2022-10-03::01:00 | 1503.134            |
| 2022-10-03::02:00 | 1512.490            |
| 2022-10-03::03:00 | 1498.982            |
| ...               | ...                 |
| 2022-10-03::11:00 | 1578.301            |
| 2022-10-04::00:00 | 1582.429            |
| 2022-10-04::01:00 | 1590.673            |
| ----------------- | ------------------- |


In the same Python console:
```python
import numpy
X = numpy.asarray([datetimes, predictions])
filename = "/tmp/predictions.csv"
numpy.savetxt(filename, X, delimiter=",", header="Datetime,predicted-ETH-value")
```

### 4.2 Put the csv online

Here's one way, using github CLI. (Use whatever you wish:)

Open a new console, and do the following. Fill in <username> with your github username, and chooose a name of your new github repo with <reponame>.
```console
#Create a new repository, with predictions.csv as the initial file
git init
mv /tmp/predictions.csv .
git add predictions.csv
git commit -m "first commit"
git remote add origin git@github.com:<username>/<reponame>.git
git push -u origin master
```

Your csv can be found at this url:
```text
https://raw.githubusercontent.com/<username>/<reponame>/main/predictions.csv
```

### 4.3 Publish (the csv) as an Ocean asset

In the same python console:
```python
# Specify metadata
date_created = "2022-09-20T10:55:11Z"
metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "ETH predictions",
    "name": "ETH predictions",
    "type": "dataset",
    "author": "<your name>",
    "license": "CC0: PublicDomain",
}


# Set the url, create UrlFile object
url=<your csv url>

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

data_nft = asset.nft
datatoken = asset.datatokens[0]

print(f"Asset created, with name: {data_nft.token_name()}")
print(f"  did: {asset.did}")
print(f"  data_NFT.address: {data_nft.address}")
print(f"  datatoken.address: {datatoken.address}")
```

Take note of the did; you'll need to include it when you enter the competition via Questbook.


## 5.  Share csv access to the competition organizers

In the same Python console:
```python
#this is the official organizer address
organizer_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E"

#mint tokens into the account. >1 to make it organizers to share amongst each other.
datatoken.mint(
    account_address=organizer_address,
    value=ocean.to_wei(10),
    from_wallet=bob_wallet,
)
```
