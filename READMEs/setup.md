# Overview

This guide describes how to set up each of the following.

* A. Set Ethereum network & node
* B. Set metadata cache and data provider
* C. Set config file
* D. Define Ethereum account

Culminating in...

* E. Start using ocean-lib

## A. Set Ethereum network (e.g. Rinkeby) & Ethereum node (e.g. Infura)

You need to point to an Ethereum network via an Ethereum node. Here, we will use `Rinkeby` test network, by connecting to it via third-party service `Infura`.

1. Go to https://infura.io and sign up 

2. At Infura site, create a new project

3. Within the project settings page, copy the "project id" value. We'll use it in the next section.

4. Finally, create an envvar that points to the network via Infura: 
```console
export NETWORK_URL=https://rinkeby.infura.io/v3/<your Infura project id>
```

## B. Set Aquarius metadata cache and data provider services

Ocean uses two more services:
* [Aquarius (Metadata cache)](https://github.com/oceanprotocol/aquarius) - REST API that caches on-chain metadata, to aid search. Typically run by a marketplace.
* [Provider](https://github.com/oceanprotocol/provider) - REST API run to serve download and compute service requests. Run by marketplace or the data publiser.

The simplest is to point to services that are already running. Here are the ones for Rinkeby. (There are also ones for Ethereum mainnet.)

```console
export AQUARIUS_URL=https://aquarius.rinkeby.v3.dev-ocean.com
export PROVIDER_URL=https://provider.rinkeby.v3.dev-ocean.com
```

Alternatively, you can run your own services. We're not going to do that in the main flow here, but here's how you would.

* In a new terminal: `docker run oceanprotocol/provider:latest`
* In another new terminal: `docker run oceanprotocol/aquarius:latest`
* In your main terminal, set envvars to point to them:
```console
export AQUARIUS_URL=http://127.0.0.1:5000
export PROVIDER_URL=http://127.0.0.1:8030
```

## C. Create a config file

You need to set `NETWORK_URL`, `AQUARIUS_URL`, and `PROVIDER_URL` somehow. 

Above, you set these values using envvars. However, you can also set them in a config file. Let's do that!

1. Create an envvar to point to the config file. In your terminal: `export CONFIG_FILE=config.ini`
1. Create the file itself, named e.g. `config.ini`
3. Fill the new file like the following:

```bash
[eth-network]
network = https://rinkeby.infura.io/v3/<your Infura project id>

[resources]
aquarius.url = https://aquarius.rinkeby.v3.dev-ocean.com
provider.url = https://provider.rinkeby.v3.dev-ocean.com
```

4. Values set by envvars override values set in config files (important!). Therefore, to use the config file values, we need to get rid of the envvars we'd set above. In your terminal: ```unset NETWORK_URL AQUARIUS_URL PROVIDER_URL```

## D. Set Ethereum account

1. **Get private key.** First, you'll need an account. At its core, this is defined by its private key.
2. **Choose key's access.** Once you have a private key, you can choose how it's accessed in the code

### 1. Get private key

If you're testing on Rinkeby, you may already have an Ethereum wallet holding some Rinkeby ETH. If you do, great, use that! Use the wallet's built-in functionality to export the private key.

If you don't yet have an account, you can generate one with code using web3.py. Conveniently, it's included in ocean-lib.
```python
from ocean_lib.ocean.ocean import Ocean
ocean = Ocean()
new_account = ocean.web3.eth.account.create()
private_key = new_account.privateKey
```

Web3.py's docs have more info on Web3 account management, [here](https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.accounts).

### 1. Define account via private key

First, make your key available as an envvar. Here's an example key (you'll want your own, of course). From your console:

```console
export MY_TEST_KEY=0xaefd8bc8725c4b3d15fbe058d0f58f4d852e8caea2bf68e0f73acb1aeec19baa
```

The Ethereum address that gets computed from the example key is `0x281269C18376010B196a928c335E495bd05eC32F`.

In Python, you'd create a wallet from this private key with a line like the following. (We'll use it in the full example farther down.)

```python
wallet = Wallet(web3, private_key=os.getenv('MY_TEST_KEY'))
```

Note: Don't store your private key directly in code or deploy the example key in production, unless you want to see someone steal your funds. That's why we have it as an envvar.

### 2. Define account via **keyfile json object**

Here's an example keyfile JSON object, aka EncryptedKey. This example has the same private key as above, and password `OceanProtocol` to encrypt/decrypt the private key. The private key is stored as parameter `ciphertext` (in encrypted form, of course).

```
{
  "address": "281269c18376010b196a928c335e495bd05ec32f",
  "crypto": {
    "cipher": "aes-128-ctr",
    "cipherparams": {
      "iv": "ac0b74c5100bd319030d983029256250"
    },
    "ciphertext": "6e003d25869a8f84c3d055d4bda3fd0e83b89769b6513b58b2b76d0738f2ab1c",
    "kdf": "pbkdf2",
    "kdfparams": {
      "c": 1000000,
      "dklen": 32,
      "prf": "hmac-sha256",
      "salt": "423c1be88c1fadd926c1b668a5d93f74"
    },
    "mac": "6b90720ddc10d457c2e3e7e1b61550d7a7fa75e6051cb1ed4f1516fba4f0a45f"
  },
  "id": "7954ec59-6819-4e3c-b065-e6f3a9c1fe6c",
  "version": 3
}
```

Here's how you use the JSON object. In your console, export the EncryptedKey and password:

```console
export MY_TEST_ENCRYPTED_KEY='{"address": "281269c18376010b196a928c335e495bd05ec32f", "crypto": {"cipher": "aes-128-ctr", "cipherparams": {"iv": "ac0b74c5100bd319030d983029256250"}, "ciphertext": "6e003d25869a8f84c3d055d4bda3fd0e83b89769b6513b58b2b76d0738f2ab1c", "kdf": "pbkdf2", "kdfparams": {"c": 1000000, "dklen": 32, "prf": "hmac-sha256", "salt": "423c1be88c1fadd926c1b668a5d93f74"}, "mac": "6b90720ddc10d457c2e3e7e1b61550d7a7fa75e6051cb1ed4f1516fba4f0a45f"}, "id": "7954ec59-6819-4e3c-b065-e6f3a9c1fe6c", "version": 3}'
export MY_TEST_PASSWORD=OceanProtocol
```

In Python, you'd create a wallet from this info with a line like:
```python
wallet = Wallet(web3, encrypted_key=os.getenv('MY_TEST_ENCRYPTED_KEY'), password=os.getenv('MY_TEST_PASSWORD'))
```

## E. Start using ocean-lib

Let's put it all together in Python. 

First, configure the components.
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

Then, create an `Ocean` instance.
```python
from ocean_lib.ocean.ocean import Ocean
ocean = Ocean()
```

Then, create a `Wallet`. It will leverage the `web3` instance in the Ocean instance.
```python
#create wallet, leveraging ocean.web3
from ocean_lib.web3_internal.wallet import Wallet
wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY')) #or use keyfile approach
```

Finally, create a datatoken. As it's a transaction on the network, it will take several seconds to go through.
```
datatoken = ocean.create_data_token('Dataset name', 'dtsymbol', from_wallet=wallet)
print(f'created new datatoken with address {datatoken.address}')
``` 

It's successfully completed if it says "created new datatoken...". Congrats!

Or, if you got an error like "insufficient funds for gas", it's because your account doesn't have ETH to pay for gas. The example key that we provide doesn't, sorry, it would get eaten too quickly. ᗧ···ᗣ···ᗣ·· . But no worries! You can get some Rinkeby ETH from [this faucet](https://faucet.rinkeby.io/). 

One final thing: sometimes you will need Rinkeby OCEAN. [Here's](https://faucet.rinkeby.oceanprotocol.com/) a faucet. Have fun!
