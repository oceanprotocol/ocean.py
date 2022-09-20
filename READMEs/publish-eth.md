<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Historical ETH Price

This quickstart describes a flow to publish Binance API's historical ETH price as a free Ocean data asset.

Here are the steps:

1.  Setup
2.  Alice publishes the data asset
3.  Alice creates the dispenser

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
- [x] Setup in Python

## 2. Alice publishes the data asset

Then in the same python console:
```python
# Specify metadata
date_created = "2022-09-20T10:55:11Z"
metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Binance API v3 klines",
    "name": "Branin API v3 klines",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# Specify start/end times for prices of the previous week
from datetime import datetime, timedelta
end_datetime = datetime.now() 
start_datetime = end_datetime - timedelta(days=7) 

# Set the url
url="https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&startTime={int(start_datetime.timestamp())*1000}&endTime={int(end_datetime.timestamp())*1000}"

# Create the UrlFile object 
from ocean_lib.structures.file_objects import UrlFile
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

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")
```

### 3. Alice creates the dispenser

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

### 4. Alice gets an access token from dispenser

(Note: we'll move this to the predict-eth README shortly)

In the same Python console:
```python
amt_dispense = 1
ocean.dispenser.dispense_tokens(
    datatoken=datatoken, amount=ocean.to_wei(amt_dispense), consumer_wallet=alice_wallet
)
bal = ocean.from_wei(datatoken.balanceOf(alice_wallet.address))
print(f"Alice just got a token dispensed to her. She now holds {bal} tokens")
```