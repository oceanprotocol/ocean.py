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

Fees are defined for `polygon` & `mumbai` networks.

```python
from ocean_lib.web3_internal.utils import get_gas_fees

priority_fee, max_fee = get_gas_fees()
```

## 3. Alice publishes the asset using gas strategy

The gas strategy can be added to any `tx_dict`, and this is just an example of usage.
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
tx_dict = {
        "from": alice,
        "maxPriorityFeePerGas": priority_fee,
        "maxFeePerGas": max_fee,
}

#create data asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(
    name,
    url,
    tx_dict=tx_dict
)

#print
print("Just published a data asset:")
print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
print(f"  did={ddo.did}")
```

