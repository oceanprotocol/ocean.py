# Developers on ocean-lib-py

Compile, test, and deploy Ocean datatokens with the help of [Brownie](https://eth-brownie.readthedocs.io). 

How library works: ocean.createDataToken() calls Factory's ABI. The Factory contract deploys a new proxy contract, using the blockchain (It *won't* use Brownie to deploy the proxy contract)

This is currently a "developer version" of ocean-lib-py. Its user version be more stripped down: it won't have .sol contracts, or need Brownie.

Also not working yet: blob, transfer(), mint(), marketplace flow (metadata, >1 service). 

## Installation

[Install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

Get a local copy of `contracts` repo, ensure it's up to date.
```console
git clone https://github.com/oceanprotocol/ocean-contracts
cd ocean-contracts
git pull
cd -
```

Clone this repo, and `cd` into it.
```console
git clone https://github.com/oceanprotocol/ocean-lib-py
cd ocean-lib-py
```

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

Set up env't, ensure it's up to date
```console
source myenv/bin/activate
pip install -r requirements.txt 
source  ~/.ocean_vars
```

'Make' this repo. It will
* grab files from other repos
* alter them as needed for here
* compile (with the help of brownie)
```console
./make.py
```

Compile
```console
brownie compile
```

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
pytest tests/test_quickstart_simpleflow.py 
```

## Usage : Playing


Start brownie console:
```bash
brownie console
```

In brownie console:
```python
>>> dir()                                                                                                                                                                                                        
[Address, Contract, Deployer, ERC20, ERC20Pausable, ERC20Template, Factory, FeeCalculator, FeeCollector, FeeManager, Fixed, Migrations, Registry, SafeMath, Wei, a, accounts, alert, compile_source, config, dir, exit, history, interface, network, project, quit, rpc, run, web3]
>>> dir(ERC20Template)                                                                                                                                                                                           
[abi, at, bytecode, deploy, get_method, info, remove, selectors, signatures, topics, tx]
>>> dir(Factory)                                                                                                                                                                                                 
[abi, at, bytecode, deploy, get_method, info, remove, selectors, signatures, topics, tx]
>>> ERC20Template.deploy('Template', 'TEMPLATE', accounts[0].address, accounts[1].address, {'from': accounts[0]})                                                                                                
Transaction sent: 0xb8073c4a749a5cf8bfc9d9ebccc6aa07ec2376eea913723d656766ed0122451e
  Gas price: 0.0 gwei   Gas limit: 6721975
  ERC20Template.constructor confirmed - Block: 1   Gas used: 1455550 (21.65%)
  ERC20Template deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87

<ERC20Template Contract '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87'>
>>> Factory.deploy(ERC20Template[0].address, accounts[1].address, {'from': accounts[0]})                                                                                                                         
Transaction sent: 0xa6704ce76db2030177c547473e7f990d1c5e0182f54adfaa488db6db28cb23a5
  Gas price: 0.0 gwei   Gas limit: 6721975
  Factory.constructor confirmed - Block: 2   Gas used: 426269 (6.34%)
  Factory deployed at: 0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6

<Factory Contract '0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6'>
```

## Making changes

Change .sol, then update or add new tests.


