<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# About Ocean off-chain services

## Introduction

Ocean uses these off-chain services:

-   [Ocean Provider](https://github.com/oceanprotocol/provider) is for data services. Specifically, it's a REST API serving requests for two types of data services: static urls (for downloading data) and compute services. It's run by the marketplace or the data publisher.
-   [Ocean Aquarius](https://github.com/oceanprotocol/aquarius) is metadata cache REST API. This helps to aid search in marketplaces.

We now describe how to use these, for each of:

- Local Services: Default
- Local Services: Non-Default
- Remote Services: Default
- Remote Services: Non-Default

### Local Services: Default

When you follow [local setup](READMEs/setup-local.md), you will use Barge. Barge runs its own Ganache, and also its own Provider and Aquarius. You don't need to do more.

### Local Services: Non-Default

Instead of pointing to existing services (in Barge), you can run your own. Here's how.

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

Remember, here's how the config dict is set.
```python
from ocean_lib.example_config import get_config_dict
config = get_config_dict("mumbai") # returns a dict
# (then, here you can update the config dict as you wish)
ocean = Ocean(config)
```

### Remote Services: Default

For convenience, Ocean Protocol Foundation (OPF) runs an instance of Provider, and of Aquarius. [Ocean network docs](https://docs.oceanprotocol.com/core-concepts/networks) gives the urls.

When you follow [remote setup](READMEs/setup-remote.md), it will default to use these OPF-run Provider and Aquarius. You don't need to do more.


### Remote Services: Non-Default

You can run your own Provider or Aquarius, like shown above. And then point to it from your config dict.

You can also point to a Provider or Aquarius instance run by a 3rd party. Simply point to it from your config dict.
