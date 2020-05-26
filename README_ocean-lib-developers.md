# ocean-lib-py

Compile, test, and deploy Ocean datatokens with the help of [Brownie](https://eth-brownie.readthedocs.io). Datatokens are ERC20 tokens with an extra 'blob' parameter.

Note: we don't use a Factory contract here. It just deploys the tokens individually.

# Setup

## New Session: Installation

[Install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

Then `git clone` this repo, and `cd` into it.

Initalize virtual env't:
```console
python -m venv myenv
```

Activate environment, update it:
```console
source myenv/bin/activate 
pip install -r requirements.txt 
```

Set up private data that we can't have living on GitHub. It sets in `OCEAN_PRIVATE_KEY1`, `OCEAN_PRIVATE_KEY2`, and `WEB3_INFURA_PROJECT_ID`. If you plan to use infura and don't yet have an account, get one. 
```console
cp ocean_vars_template ~/.ocean_vars
<<change values of the env't vars>>
source ~/.ocean_vars
```

## New Session: Already Installed

```console
source myenv/bin/activate 
source  ~/.ocean_vars
```

## End Session
To deactivate environment:
```console
deactivate
```

## Usage: Compilation

This usually happens automatically. Here's the manual way, if needed:
```bash
brownie compile
```

## Usage: Testing

```bash
brownie test
```

## Usage : Does quickstart work?

```console
python quickstart.py
```


## Usage : Playing


Start brownie console:
```bash
brownie console
```

In brownie console:
```python
>>> dt = Datatoken.deploy("DT1", "Datatoken 1", "123.com", 18, 100, {'from': accounts[0]})                                                                                                                 
Transaction sent: 0x9d20d3239d5c8b8a029f037fe573c343efd9361efd4d99307e0f5be7499367ab
  Gas price: 0.0 gwei   Gas limit: 6721975
  Datatoken.constructor confirmed - Block: 1   Gas used: 601010 (8.94%)
  Datatoken deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87

>>> dt.blob()                                                                                                                                                                                              
'123.com'
```

## Making changes

Change .sol, then update or add new tests.

# Quickstart snippet

## 1. Alice publishes a dataset (= publishes a datatoken contract)

For now, you're Alice:) Let's proceed.

```python
from ocean_lib import Ocean
config = {
   'network' : 'rinkeby',
   'privateKey' : '8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f',
}
ocean = Ocean(config)
account = ocean.accounts.list()[0]
token = ocean.datatoken.create('localhost:8030',account)
dt_address = token.getAddress()
print(dt_address)
```
