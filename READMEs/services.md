<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# About Ocean off-chain services

## Introduction

Ocean uses these off-chain services:

-   [Ocean Provider](https://github.com/oceanprotocol/provider) is for data services. Specifically, it's a REST API serving requests for two types of data services: static urls (for downloading data) and compute services. It's run by the marketplace or the data publisher.
-   [Ocean Aquarius](https://github.com/oceanprotocol/aquarius) is metadata cache REST API. This helps to aid search in marketplaces.

We now describe how to use these.

## 1. Set config values for services

Here we set the config  dict. You can use boilerplate from example config.

```python
import os
from ocean_lib.example_config import get_config_dict

# configure the components
config = get_config_dict()
```

Now you're ready to use the services! 🐳 The marketplace tutorial will use them in more detail.

## Alternatives on Services

Above, we described a specific flow to go through configuring services. Here are some variants of that flow.

### Point to services in other networks

The service urls above are for Goerli. [Ocean's docs have urls](https://docs.oceanprotocol.com/core-concepts/networks) for Ethereum mainnet and other supported networks.

### Run your own services, separately

Above, we pointed to existing services. Alternatively, you can run your own. Here's how.

Open a new console, and get provider running:

```console
docker run oceanprotocol/provider:latest
```

Open another new console, and get aquarius running:

```console
docker run oceanprotocol/aquarius:latest
```

Here are the urls for the local services, for use in the config dict.

-   Provider url: `http://127.0.0.1:8030`
-   Aquarius url: `http://127.0.0.1:5000`

### Run your own services, all at once

Above, we ran all services separately. You can also run [Ocean Barge](https://github.com/oceanprotocol/barge) to conveniently run them all at once.
