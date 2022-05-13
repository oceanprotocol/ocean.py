<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# On Config Parameters

We can set any config parameter (a) via an envvar, or (b) via a config file. Envvar values override config file values.

An `Ocean` instance will hold a `Config` instance that holds various config parameters. These parameters need to get set. This is set based on what's input to `Ocean` constructor:

1.  dict input: `Ocean({'network':..})`
2.  Config object input: `Ocean(Config('config.ini'))`
3.  no input, so it uses OCEAN_CONFIG_FILE envvar

Here are examples.

## 1. dict input, filled from envvars

First, in console:

```console
export OCEAN_NETWORK_URL=https://rinkeby.infura.io/v3/<your Infura project id>
export METADATA_CACHE_URI=https://v4.aquarius.oceanprotocol.com
export PROVIDER_URL=https://v4.provider.rinkeby.oceanprotocol.com
```

Then, do the following in Python. The `Ocean` constructor takes a `dict`, which in turn is set by envvars.

```python
import os
from ocean_lib.ocean.ocean import Ocean
d = {
   'network' : os.getenv('OCEAN_NETWORK_URL'),
   'metadataCacheUri' : os.getenv('METADATA_CACHE_URI'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(d)
```
For legacy support, you can also use `metadataStoreUri` instead of `metadataCacheUri`.

## 1a. Unsetting envvars

Recall that parameters set by envvars override config file values. So, to use a config value in a file, we must remove its envvar.

Here's how. In the console:

```console
    unset OCEAN_NETWORK_URL METADATA_CACHE_URI AQUARIUS_URL PROVIDER_URL
```

## 2. Config object input, filled from config file

First, in your working directory, create `config.ini` file and fill as follows:

```console
    [eth-network]
    network = https://rinkeby.infura.io/v3/<your infura project id>

    [resources]
    metadata_cache_uri = https://v4.aquarius.oceanprotocol.com
    provider.url = https://v4.provider.rinkeby.oceanprotocol.com
```

Then, in Python:

```python
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
c = Config('config.ini')
ocean = Ocean(c)
```

## 3. No input, so it uses OCEAN_CONFIG_FILE envvar

We'll use the `config.ini` file created from the previous example.

Then, set an envvar for the config file. In the console:

```console
export OCEAN_CONFIG_FILE=config.ini
```

Then, in Python:

```python
import os

from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
c = Config(os.getenv("OCEAN_CONFIG_FILE"))
ocean = Ocean(c)
```

## Further details

The file [config.py](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/config.py) lists all the config parameters.

For the most precise description of config parameter logic, see the [Ocean() constructor implementation](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/ocean/ocean.py).
