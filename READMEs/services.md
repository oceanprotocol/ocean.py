# About Ocean off-chain services

## Introduction

Ocean uses these off-chain services:
* [Ocean Provider](https://github.com/oceanprotocol/provider) for data services. A REST API run to serve download and compute service requests. Run by marketplace or the data publisher.
* [Ocean Aquarius](https://github.com/oceanprotocol/aquarius) metadata cache. A REST API that caches on-chain metadata, to aid search. Typically run by a marketplace.

We now describe how to use these.

## 1. Create a config file

In your working directory, create a file `config.ini` and fill it with the following. It points to the infura id that you created in the previous tutorial, and the urls for off-chain services (Provider, Aquarius).
```
[eth-network]
network = https://rinkeby.infura.io/v3/<your Infura project id>

[resources]
aquarius.url = <your aquarius url>
provider.url = <your provider url>
```

Create an envvar to point to the new file. In the console:
```console
export CONFIG_FILE=config.ini
```

## 2. Use the services within Python

In Python, import and configure the components / services:
```python
import os
from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.contract_handler import ContractHandler

#configure the components
config = Config(os.getenv('CONFIG_FILE'))
ConfigProvider.set_config(config)
Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
ContractHandler.set_artifacts_path(config.artifacts_path)
```

Now you're ready to use the serivces. The marketplace tutorial will use them in more detail.

## Alternatives on Services

Above, we described a flow to go through configuring services. Here are some variants.

### Point to services in other networks

The service urls above are for rinkeby. [Ocean docs list other supported networks](https://docs.oceanprotocol.com/concepts/networks-overview/) like Ethereum mainnet and ropsten, along with associated urls.

### Run your own services

Above, we pointed to existing services. Alternatively, you can run your own. Here's how.

Open a new console, and get provider running:
```console
docker run oceanprotocol/provider:latest
```

Open another new console, and get aquarius running:
```console
docker run oceanprotocol/aquarius:latest
```

Here are the urls for the local services, for use in `config.ini` etc.
* Provider url: `http://127.0.0.1:8030`
* Aquarius url: `http://127.0.0.1:5000`

## Alternatives on Parameter Setting

We can set any parameter as an envvar, rather than with `config.ini'. Here's an example.

First, in console:
```console
export NETWORK_URL=https://rinkeby.infura.io/v3/<your Infura project id>
export AQUARIUS_URL=<your aquarius url>
export PROVIDER_URL=<your provider url>
```

Then, do the following in Python. In this case, the `Ocean` constructor takes a `config` dict, which in turn is set by envvars.
```python
import os
from ocean_lib.ocean.ocean import Ocean
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(config)
```

Note: Values set by envvars override values set in config files (important!). Therefore, to use the config file values, we need to get rid of the envvars, in the console: `unset NETWORK_URL AQUARIUS_URL PROVIDER_URL`.