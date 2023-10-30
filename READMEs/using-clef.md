<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Using hardware wallets with ocean.py

This README describes how to setup ocean.py with hardware wallets.

We assume you've already (a) [installed Ocean](install.md), configured any environment variables necessary and created the Ocean object as described in (b) done [local setup](setup-local.md) or [remote setup](setup-remote.md).
These instructions are applicable to both local and remote setup. If you intend to use hardware wallets ONLY, then you can skip the wallet creation parts in the setup instructions.

## 1. Setting up and running Clef
ocean.py allows the use of hardware wallets via [Clef](https://geth.ethereum.org/docs/clef/tutorial), an account management tool included within [Geth](https://geth.ethereum.org/)

To use a hardware wallet with ocean.py, start by [installing Geth](https://geth.ethereum.org/docs/install-and-build/installing-geth).
Once finished, type the following command in a bash console and follow the on-screen prompts to set of Clef:

```console
clef init
```

If you need to create a new account, you can use the command `clef newaccount`. For other usefull commands, please consult the [Clef documentation](https://geth.ethereum.org/docs/tools/clef/introduction).

Once Clef is configured, run it in a bash console as needed, i.e.

```console
# you can use a different chain if needed
clef --chainid 8996
```

You can also customise your run, e.g. `clef --chainid 8996 --advanced`.

Keep the clef console open, you will be required to approve transactions and input your password when so requested.

## 2. Connect ocean.py to Clef via Brownie

In your Python console where you have setup the Ocean object:

```python
from ocean_lib.web3_internal.clef import get_clef_accounts
clef_accounts = get_clef_accounts()
```

Approve the connection from the Clef console. This will add your Clef account to the `accounts` array.
You can now use the Clef account instead of any wallet argument, e.g. when publishing or consuming DDOs.


```python
# pick up the account for convenience
clef_account = clef_accounts[index]

# make sure account is funded. Let's transfer some ether and OCEAN from alice
from ocean_lib.ocean.util import send_ether
send_ether(config, alice, clef_account.address, to_wei(4))
OCEAN.transfer(clef_account, to_wei(4), {"from": alice})

# publish and download an asset
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": clef_account})
datatoken.mint(clef_account, to_wei(1), {"from": clef_account})
order_tx_id = ocean.assets.pay_for_access_service(ddo, {"from": clef_account})
ocean.assets.download_asset(ddo, clef_account, './', order_tx_id)

```

Please note that you need to consult your clef console periodically to approve transactions and input your password if needed.
You can use the ClefAccount object seamlessly, in any transaction, just like regular Accounts. Simply send your transaction with `{"from": clef_account}` where needed.
