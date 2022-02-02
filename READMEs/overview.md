<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

At the high level, the main ocean-lib features are accessible via the `Ocean` instance. Here is a
quick overview of the main functions and submodules:

```python
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.example_config import ExampleConfig

config = ExampleConfig.get_config()

# Ocean instance: create/get datatoken, get dtfactory, user orders (history)
ocean = Ocean(config)

# Then use the following submodules...

# Assets: publish, get, list, search, order, consume/download
ocean.assets

# Datatoken Pool: create, add/remove liquidity, check liquidity, price, buy datatokens
ocean.pool

# Fixed rate exchange: create, price, buy datatokens
ocean.exchange

# Compute-to-data: consume/start, stop, results, status, define-service
ocean.compute
```

To access functions that are not supported in the above classes, you can directly use the lower
level objects:

```python
# BPool -- Balancer pool
from ocean_lib.models.bpool import BPool
BPool(web3, pool_address)

```
