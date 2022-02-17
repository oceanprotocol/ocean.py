<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# On Config Parameters

We can set any config parameter (a) via an envvar, or (b) via a config file. Envvar values override config file values.

An `Ocean` instance will hold a `Config` instance that holds various config parameters. These parameters can be set in a variety of ways:

1. Config object input
    * Filled from ExampleConfig: `Ocean(ExampleConfig.get_config())` (recommended)
    * Filled from config file: `Ocean(Config('config.ini'))`
    * Filled from config file specified by `OCEAN_CONFIG_FILE` envvar: `Ocean(Config())`
    * Filled from config dict: `Ocean(Config('network':..}))`
2.  dict input: `Ocean({'network':..})` (deprecated because it doesn't support all config options)

Here are examples.

## 1a. Config object input, filled from ExampleConfig (recommended)

First, in console:

```console
export OCEAN_NETWORK_URL=https://rinkeby.infura.io/v3/<your Infura project id>
```

Then, in Python:

```python
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)
```

## 1b. Config object input, filled from config file

First, in your working directory, create `config.ini` file and fill as follows:

```console
    [eth-network]
    network = https://rinkeby.infura.io/v3/<your infura project id>
    block_confirmations = 1

    [resources]
    metadata_cache_uri = https://aquarius.oceanprotocol.com
    provider.url = https://provider.rinkeby.oceanprotocol.com
```

Then, in Python:

```python
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
config = Config('config.ini')
ocean = Ocean(config)
```

## 1c. Config object input, filled using `OCEAN_CONFIG_FILE` envvar

We'll use the `config.ini` file created in 1b (above).

Then, set an envvar for the config file. In the console:

```console
export OCEAN_CONFIG_FILE=config.ini
```

Then, in Python:

```python
import os

from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
config = Config()
ocean = Ocean(config)
```

## 1d. Config object input, filled using config dict

In python:

```python
from ocean_lib.ocean.ocean import Ocean
config_dict = {
    'eth-network' : {
        'network' : 'https://rinkeby.infura.io/v3/<your Infura project id>',
        'block_confirmations' : 1,
    },
    'resources' : {
        'metadataCacheUri' : 'https://aquarius.oceanprotocol.com',
        'providerUri' : 'https://provider.rinkeby.oceanprotocol.com',
    },
}
config = Config(options_dict=config_dict)
ocean = Ocean(config)
```

## 2. dict input (deprecated because it doesn't support all config options)

In python:

```python
from ocean_lib.ocean.ocean import Ocean
config_dict = {
   'network' : 'https://rinkeby.infura.io/v3/<your Infura project id>',
   'metadataCacheUri' : 'https://aquarius.oceanprotocol.com',
   'providerUri' : 'https://provider.rinkeby.oceanprotocol.com',
}
ocean = Ocean(config_dict)
```

For legacy support, you can also use `metadataStoreUri` instead of `metadataCacheUri`.


## Appendix: Unsetting envvars

Recall that parameters set by envvars override config file values. So, to use a config value in a file, we must remove its envvar.

Here's how. In the console:

```console
    unset OCEAN_NETWORK_URL METADATA_CACHE_URI AQUARIUS_URL PROVIDER_URL
```

## Further details

* [example_config.py](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/example_config.py) contains the default config values that differ depending on the `chain_id`.
* [config.py](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/config.py) lists all the config parameters.
* [Ocean() constructor implementation](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/ocean/ocean.py) shows the most precise description of config parameter logic.
