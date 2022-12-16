<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# On Config Parameters

We can set any config parameter using the config dictionary.

An `Ocean` instance will hold a `config_dict` that holds various config parameters. These parameters need to get set. This is set based on what's input to `Ocean` constructor:

1.  dict input: `Ocean({'METADATA_CACHE_URI':..})`
2.  use boilerplate from example config

Here are examples.

## 1. dict input, filled from envvars

```python
import os
from ocean_lib.ocean.ocean import Ocean
d = {
   'METADATA_CACHE_URI': "https://v4.aquarius.oceanprotocol.com",
   'PROVIDER_URL' : "https://v4.provider.goerli.oceanprotocol.com",
}
ocean = Ocean(d)
```

## Further details

For the most precise description of config parameter logic, see the [Ocean() constructor implementation](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/ocean/ocean.py).
