<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish API of Historical ETH Price

This quickstart describes a flow to publish Binance API of historical ETH price, to make it available as free data asset on Ocean, and to consume it.

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

Then in the same python console:
```python
# Specify metadata
date_created = "2022-09-20T10:55:11Z"
name = "Binance API v3 klines"
metadata = {
  "name": name, "description": name, "author": "Trent", "type": "dataset",
  "created": date_created,  "updated": date_created, "license": "CC0: PublicDomain"
}

# Set the url
from datetime import datetime, timedelta
end_datetime = datetime.now() 
start_datetime = end_datetime - timedelta(days=7) #the previous week

from ocean_lib.structures.file_objects import UrlFile
url = f"https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={int(start_datetime.timestamp())*1000}&endTime={int(end_datetime.timestamp())*1000}"
url_file = UrlFile(url)

# Publish dataset. It creates the data NFT, datatoken, and fills in metadata
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    [url_file],
    datatoken_templates=[1],
    datatoken_names=["Datatoken 1"],
    datatoken_symbols=["DT1"],
    datatoken_minters=[alice_wallet.address],
    datatoken_fee_managers=[alice_wallet.address],
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

### 3. Alice makes the API asset available for free, via a dispenser

In the same Python console:
```python
datatoken.create_dispenser(
    dispenser_address=ocean.dispenser.address,
    max_balance=ocean.to_wei(10000),
    max_tokens=ocean.to_wei(10000),
    with_mint=True,
    allowed_swapper=ZERO_ADDRESS,
    from_wallet=alice_wallet,
)

dispenser_status = ocean.dispenser.status(datatoken.address)
assert dispenser_status[0:2] == (True, alice_wallet.address, True)

For an example of consuming this data, see the [predict-eth flow][READMEs/predict-eth.md].


### 4.  Bob consumes the API asset

Now, you're Bob. All you have is the did of the data asset; you compute the rest.

In the same Python console:
```python
# Set asset did. Practically, you'd get this from Ocean Market.
# In this flow, you can get it from the printout of the steps above.
asset_did = asset.did

# Retrieve the Asset, data_nft, and datatoken objects
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

The file downloaded is a .json. From that, use the python `json` library to parse it as desired.

Bob can verify that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```


### Appendix. Details of Binance API data

Docs for Binance Kline/Candlestick Data API are [here](https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data).

Here's an example of grabbing the data given a url. The url specifies 7 days.

```python
import requests
req_s = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime=1663110211000&endTime=1663715011000"
res = requests.get(req_s)
data = res.json() #list of lists

print(data)
# returns:
# [[1663113600000,"1574.40000000","1647.01000000","1552.38000000","1638.39000000","764562.53930000",1663199999999,"1222499363.04636600",1088561,"401130.51880000","641555247.03558200","0"],[1663200000000,"1638.40000000","1655.20000000","1458.00000000","1472.75000000","1335499.80470000",1663286399999,"2095367507.33233400",1748683,"677767.22230000","1065686121.99748000","0"],[1663286400000,"1472.76000000","1483.35000000","1405.52000000","1433.90000000","693597.24250000",1663372799999,"1006033555.19748100",1111984,"339284.67190000","492281156.22353200","0"],[1663372800000,"1433.90000000","1476.13000000","1409.12000000","1468.83000000","421391.37430000",1663459199999,"608805593.71431500",694945,"214030.86210000","309280515.75244900","0"],[1663459200000,"1468.82000000","1469.63000000","1325.55000000","1334.51000000","804113.46800000",1663545599999,"1118416540.56069700",990605,"389497.83390000","541430482.23444900","0"],[1663545600000,"1334.51000000","1393.35000000","1280.00000000","1375.98000000","974855.19800000",1663631999999,"1293086590.94143200",1235360,"490443.56970000","650755506.31086900","0"],[1663632000000,"1375.98000000","1384.78000000","1312.71000000","1321.54000000","641357.58960000",1663718399999,"867278414.69410100",954588,"318605.63970000","430884515.51174400","0"]]

# entry 4 is "close price", which we can treat as spot price. Binance docs have details.
spot_prices = [float(x[4]) for x in data]

#make a 2D array of all data
import numpy
D = numpy.asarray(data)
print(D.shape)
# returns:
# (7,12)
```







