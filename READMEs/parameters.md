# Parameter Setting Options: Envvars vs config files

We can set any parameter as
1. an envvar, *or*
1. with a config file like `config.ini`

Values set by envvars override values set in config files (important!). Therefore, to use the a config file value, we need to get rid of its envvar. E.g. in the console: `unset NETWORK_URL`.

## 1. Example with envvars

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

## 2. Example with config.ini

First, in your working directory, create `config.ini` file and fill as follows:
```
[eth-network]
network = https://rinkeby.infura.io/v3/<your infura project id>

[resources]
aquarius.url = https://provider.rinkeby.v3.dev-ocean.com
provider.url = https://aquarius.rinkeby.v3.dev-ocean.com
```

Then, do the following in Python. In this case, the `Ocean` constructor takes no arguments.
```python
from ocean_lib.ocean.ocean import Ocean
ocean = Ocean()
```
