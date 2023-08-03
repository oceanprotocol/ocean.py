<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Local Setup

Here, we do setup for local testing.

We assume you've already [installed Ocean](install.md).

## 1. Download barge and run services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

Barge helps you quickly become familiar with Ocean, because the local blockchain has low latency and no transaction fees. Accordingly, many READMEs use it. However, if you plan to only use Ocean with remote services, you don't need barge.

Note: if you are running MacOS or Windows, we recommend to go directly to [Remote Setup](setup-remote.md). Why: Barge uses Docker, which behaves badly on MacOS and Windows. We're working to address this [here](https://github.com/oceanprotocol/ocean.py/issues/1313).

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh
```

Now that we have barge running, we can mostly ignore its console while it runs.

## 2. Set envvars

From here on, go to a console different than Barge. (E.g. the console where you installed Ocean, or a new one.)

First, ensure that you're in the working directory, with venv activated:

```console
cd my_project
source venv/bin/activate
```

Then, set keys in readmes. As a Linux user, you'll use "`export`". In the same console:

```console
# keys for alice and bob in readmes
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc
export TEST_PRIVATE_KEY3=0x732fbb7c355aa8898f4cff92fa7a6a947339eaf026a08a51f171199e35a18ae0


# key for minting fake OCEAN
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

## 3. Setup in Python

In the same console, run Python console:
```console
python
```

In the Python console:
```python
# Create Ocean instance
from ocean_lib.example_config import get_config_dict
config = get_config_dict("development")

from ocean_lib.ocean.ocean import Ocean
ocean = Ocean(config)

# Create OCEAN object. Barge auto-created OCEAN, and ocean instance knows
OCEAN = ocean.OCEAN_token

# Mint fake OCEAN to Alice & Bob
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

# Create Alice's wallet
import os
from eth_account import Account

alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
alice = Account.from_key(private_key=alice_private_key)
assert ocean.wallet_balance(alice) > 0, "Alice needs ETH"
assert OCEAN.balanceOf(alice) > 0, "Alice needs OCEAN"

# Create additional wallets. While some flows just use Alice wallet, it's simpler to do all here.
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob = Account.from_key(private_key=bob_private_key)
assert ocean.wallet_balance(bob) > 0, "Bob needs ETH"
assert OCEAN.balanceOf(bob) > 0, "Bob needs OCEAN"

carlos_private_key = os.getenv('TEST_PRIVATE_KEY3')
carlos = Account.from_key(private_key=carlos_private_key)
assert ocean.wallet_balance(carlos) > 0, "Carlos needs ETH"
assert OCEAN.balanceOf(carlos) > 0, "Carlos needs OCEAN"


# Compact wei <> eth conversion
from ocean_lib.ocean.util import to_wei, from_wei
```

## 4. Next step

You've now set up everything you need for local testing, congrats!

The next step - the fun one - is to walk through the [main flow](main-flow.md). In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

Because you've set up for local, you'll be doing all these steps on the local network.
