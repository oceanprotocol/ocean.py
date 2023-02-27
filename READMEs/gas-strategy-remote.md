<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Use Specific Gas Strategy for Remote Networks

This quickstart illustrates the definition of gas strategy in ocean-lib stack in order to
confirm the transactions on blockchain as soon as possible in case the network is congested.

Here are the steps:

1.  Setup
2.  Define gas strategy
3.  Alice publishes the asset using gas strategy

Let's go through each step.

## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up remotely](setup-remote.md).

## 2. Define gas strategy

Fees are defined for `polygon-main` & `polygon-test` networks.

```python
from tests.integration.remote.util import get_gas_fees_for_remote

priority_fee, max_fee = get_gas_fees_for_remote()
```

## 3. Alice publishes the asset using gas strategy

```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(
    name,
    url,
    {
        "from": alice,
        "priority_fee": priority_fee,
        "max_fee": max_fee,
    },
)

#print
print("Just published a data asset:")
print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
print(f"  did={ddo.did}")
```

