# Wallets

This page describes some basic approaches to Ethereum wallets and accounts.

All you really need is a private key. From that, you can derive the Ethereum address. An Ethereum "account" is a combination of private key and Eth address.

A "wallet" is a thing that stores private keys (and maybe signs transactions). This includes Metamask (browser plugin), Trezor (hardware wallet), and more. [Ocean docs on wallets](https://docs.oceanprotocol.com/tutorials/wallets/) has more information.

Here we describe:

1. How to generate private keys
1. Where to store private keys
1. How your software might access accounts

## 1. How to generate private keys

### Generate in browser with Metamask

The datatokens tutorial described how to install Metamask, then use one the Ethereum accounts it auto-generates (along with the private key).

### Generate in Python 

ocean-lib includes the [web3.py library](https://web3py.readthedocs.io/en/stable/) which can generate private keys. (Part of its [web3.py account management](https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.accounts)).

Here's how. In Python:
```python
from ocean_lib.ocean.ocean import Ocean
ocean = Ocean()
private_key = ocean.web3.eth.account.create().privateKey #some web3.py versions
private_key = ocean.web3.eth.account.create().privateKey #other web3.py versions
```

## 2. Where to store private keys

The *whole point* of crypto wallets is store private keys. Wallets have various tradeoffs of cost, convienence, and security.

It can also be useful to store private keys locally on your machine, for testing, with a small amount of value at stake.

Do *not* store your private keys on anything public, unless you want your tokens to disappear. For example, don't store your private keys in GitHub or expose them on frontend webpage code.

## 3. How your software might access Ethereum accounts

There are two main ways: (a) directly load private key, and (b) as a keyfile JSON object. Let's review each.

### 3a. Directly load private key

You could grab this from a locally-stored file, or from an envvar that you copy in for a new session. Here we focus on the latter.

First, make your key available as an envvar. Here's an example key. From your console:

```console
export MY_TEST_KEY=0xaefd8bc8725c4b3d15fbe058d0f58f4d852e8caea2bf68e0f73acb1aeec19baa
```

The Ethereum address that gets computed from the example key is `0x281269C18376010B196a928c335E495bd05eC32F`.

In Python, you'd create a wallet from this private key with a line like:

```python
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
ocean = Ocean()
wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY'))
```

### 3b. Keyfile JSON object, aka EncryptedKey

Here's an example JSON object. This example has the same private key as above, and password `OceanProtocol` to encrypt/decrypt the private key. The private key is stored as parameter `ciphertext` (in encrypted form, of course).

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
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
ocean = Ocean()
wallet = Wallet(ocean.web3, encrypted_key=os.getenv('MY_TEST_ENCRYPTED_KEY'), password=os.getenv('MY_TEST_PASSWORD'))
```

