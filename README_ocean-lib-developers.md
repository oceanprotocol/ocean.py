# ocean-lib-py

Compile, test, and deploy Ocean datatokens with the help of [Brownie](https://eth-brownie.readthedocs.io). 

How library will work:
* ocean.createDataToken() calls Factory's ABI. The Factory contract will deploy a new proxy contract, using the blockchain (It *won't* use Brownie to deploy the proxy contract)

This is currently a "developer version" of ocean-lib-py. Its user version be more stripped down: it won't have .sol contracts, or need Brownie.

## Installation

Get a local copy of `contracts` repo, ensure it's up to date.
```console
git clone https://github.com/oceanprotocol/ocean-contracts
cd ocean contracts
git pull
cd -
```

[Install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

Then `git clone` this repo, and `cd` into it.

Initalize virtual env't. Activate env't. Update modules in env't.
```console
python -m venv myenv
source myenv/bin/activate 
pip install -r requirements.txt 
```

Set up private data that we can't have living on GitHub. It sets in `OCEAN_PRIVATE_KEY1`, `OCEAN_PRIVATE_KEY2`, and `WEB3_INFURA_PROJECT_ID`. If you plan to use infura and don't yet have an account, get one. 
```console
cp ocean_vars_template ~/.ocean_vars
<<change values of the env't vars>>
source ~/.ocean_vars
```

## New Session / 'make' work

Set up env't.
```console
source myenv/bin/activate 
source  ~/.ocean_vars
```

Compile
```console
brownie compile
```

If the previous step didn't result in an ABI for the proxy contract / ERC20 contract, put one in (in interfaces/). WIP.

## End Session
To deactivate environment:
```console
deactivate
```

## Usage: Testing / Quickstart

Test all
```bash
pytest
```

Test simple flow quickstart
```bash
pytest -k simpleflow
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


