
# Custody-light flow

It allows orgs to buy & consume data without having custody of assets.

We assume you've already (a) [installed Ocean](install.md), and (b) done [local setup](setup-local.md) or [remote setup](setup-remote.md). This flow works for either one, without any changes between them (!)

This flow is split in two sections:
- free steps: publish free asset with a Datatoken 2 (enterprise template), then consume;
- priced steps: publish a priced asset attached to a Datatoken 2 (enterprise template), then buy / consume.

Let's go!


## Free steps

Steps in this flow:

1. Alice publishes a free asset
2. Bob dispenses funds from the asset's pricing schema
3. Bob consumes the asset

### 1. Alice publishes a free asset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
from ocean_lib.models.dispenser import DispenserArguments
from ocean_lib.ocean.util import to_wei

(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": alice}, use_enterprise=True, pricing_schema_args=DispenserArguments(to_wei(1), to_wei(1)))

#print
print("Just published a free asset:")
print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
print(f"  did={ddo.did}")
```

### 2. Bob dispenses funds from the asset's pricing schema

Bob wants to consume Alice's asset. He can dispense 1.0 datatokens to complete his job.
Below, we show the possible approach:

```python

provider_fees = ocean.retrieve_provider_fees(
    ddo, ddo.services[0], publisher_wallet=bob
)

tx = datatoken.dispense_and_order(provider_fees, {"from": bob}, consumer=bob.address, service_index=0)

```

### 3. Bob consumes the asset

Bob now has the transaction receipt to prove that he dispensed funds! Time to download the dataset and use it.


In the same Python console:
```python
# Bob downloads the file. If the connection breaks, Bob can try again
asset_dir = ocean.assets.download_asset(ddo, bob, './', tx.txid)

import os
file_name = os.path.join(asset_dir, "file0")
```

Let's check that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```


## Priced steps

Steps in this flow:

1. Alice publishes a priced asset
2. Bob buys funds from the asset's pricing schema
3. Bob consumes the asset

### 1. Alice publishes a free asset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
from ocean_lib.models.fixed_rate_exchange import ExchangeArguments
from ocean_lib.ocean.util import to_wei

(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": alice}, use_enterprise=True, pricing_schema_args=ExchangeArguments(
            rate=to_wei(3), base_token_addr=ocean.OCEAN_address, dt_decimals=18
        ),)

#print
print("Just published a priced asset:")
print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
print(f"  did={ddo.did}")
```

### 2. Bob buys funds from the asset's pricing schema

Bob wants to consume Alice's asset. He can buy 1.0 datatokens to complete his job.
Below, we show the possible approach:

```python

provider_fees = ocean.retrieve_provider_fees(
    ddo, ddo.services[0], publisher_wallet=bob
)
exchange = datatoken.get_exchanges()[0]
OCEAN = ocean.OCEAN_token
OCEAN.approve(
        datatoken.address,
        to_wei(10),
        {"from": bob},
)
OCEAN.approve(
    exchange.address,
    to_wei(10),
    {"from": bob},
)
tx = datatoken.buy_DT_and_order(provider_fees, exchange, {"from": bob}, consumer=bob.address, service_index=0)

```

### 3. Bob consumes the asset

Bob now has the transaction receipt to prove that he bought funds from the exchange! Time to download the dataset and use it.


In the same Python console:
```python
# Bob downloads the file. If the connection breaks, Bob can try again
asset_dir = ocean.assets.download_asset(ddo, bob, './', tx.txid)

import os
file_name = os.path.join(asset_dir, "file0")
```

Let's check that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```