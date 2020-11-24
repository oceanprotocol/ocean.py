# Overview

This page describes how to set up each of the following.

* A. Ethereum account
* B. Config file
* C. Environment variables
* D. Initialize components

Culminating in...

* E. Start using ocean-lib

## A. Ethereum account

To start with you will need an Ethereum account. Here are some options:
1. Define account via **private key**, *or*
2. Define account via **keyfile json object**. This stores the private key in json format, encrypted with a password.

### 1. Define account via private key

First, make your key available as an envvar. Here's an example key (you'll want your own, of course). From your console:

```console
export MY_TEST_KEY=0xaefd8bc8725c4b3d15fbe058d0f58f4d852e8caea2bf68e0f73acb1aeec19baa
```

Then, in your Python code, create a Wallet object and specify your private key.

```python
import os
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.wallet import Wallet
web3 = Web3Provider.get_web3()
wallet = Wallet(web3, private_key=os.getenv('MY_TEST_KEY'))
```

The Ethereum address that gets computed from the example key is `0x281269C18376010B196a928c335E495bd05eC32F`.

Note: Don't store your private key directly in code or deploy the example key in production, unless you want to see someone steal your funds.

### 2. Define account via **keyfile json object**

Here's an example JSON object aka EncryptedKey. This example has the same private key as above, and password `OceanProtocol` to encrypt/decrypt the private key. The private key is stored as parameter `ciphertext` (in encrypted form, of course).

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

Then, in your Python code, create a Wallet object and specify the EncyptedKey and password:
```python
import os
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.wallet import Wallet
web3 = Web3Provider.get_web3()
wallet = Wallet(web3, encrypted_key=os.getenv('MY_TEST_ENCRYPTED_KEY'), password=os.getenv('MY_TEST_PASSWORD'))
```

## B. Config file
In the project's root folder there is a `config.ini` file. The following config values are a must have:
```
[eth-network]
network = 'rinkeby'

[resources]

; Aquarius is the metadata cache with a REST API to search and retrieve metadata of published assets
aquarius.url = https://aquarius.rinkeby.v3.dev-ocean.com
; Provider is the REST API run by a data provider to serve download and compute service requests
provider.url = https://provider.rinkeby.v3.dev-ocean.com

```

The example above already has values that work with the ocean contracts deployed to the `Rinkeby` test net.

## C. Environment variables

Set the following envvars, in addition to the privatekey setup described above.
```console
export CONFIG_FILE=my_config.ini
```

Envvars override config file values. Therefore, you can do the following instead of using the config file. Your choice:)
```console
export NETWORK_URL=rinkeby
export AQUARIUS_URL=https://aquarius.rinkeby.v3.dev-ocean.com
export PROVIDER_URL=https://provider.rinkeby.v3.dev-ocean.com

```

## D. Initialize components
Apply the following initializations once:
```python
import os
from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.contract_handler import ContractHandler

config = Config(os.getenv(ENV_CONFIG_FILE))
ConfigProvider.set_config(config)
Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
ContractHandler.set_artifacts_path(config.artifacts_path)

```

## E. Start using ocean-lib

This example lines up a wallet, creates an Ocean instance, and publishes your first datatoken.
```python
#line up wallet, like above
import os
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.ocean.ocean import Ocean
wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY'))

#create an Ocean instance
ocean = Ocean()

#create a datatoken
datatoken = ocean.create_data_token('Dataset name', 'dtsymbol', from_wallet=wallet)
print(f'created new datatoken with address {datatoken.address}')
``` 
