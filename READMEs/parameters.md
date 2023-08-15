<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# On Config Parameters

We can set any config parameter using the config dictionary.

An `Ocean` instance will hold a `config_dict` that holds various config parameters. These parameters need to get set using the ExampleConfig class. This is set based on what's input to `Ocean` constructor:

1.  dict input: `Ocean({'METADATA_CACHE_URI':..})`, in which case you have to build the web3 instance manually
2.  use boilerplate from example config, which also sets the web3 instance to be used by each contract

## Example

Here is an example for (1): dict input, filled from envvars

```python
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.example_config import get_web3

network_url = "https://your-rpc.com"

d = {
   'METADATA_CACHE_URI': "https://v4.aquarius.oceanprotocol.com",
   'PROVIDER_URL' : "https://v4.provider.goerli.oceanprotocol.com",
   "web3_instance": get_web3(network_url)
}
ocean = Ocean(d)
```

## Further details

For the most precise description of config parameter logic, see the [Ocean() constructor implementation](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/ocean/ocean.py).
