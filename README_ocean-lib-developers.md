# Developing ocean-lib-py

This README is how to further *develop* ocean-lib-py. (Compare to the quickstarts which show how to *use* ocean-lib-py.)

Here, you can:
1. **Copy contracts** from other repos to here
1. **Compile** the contracts into ABIs etc
1. **Deploy** the contracts to {local, rinkeby, mainnet}
1. **Test** ocean-lib-py
1. (Along the way) **Debug** at the contract or py level.

These steps are detailed below. But first, installation. 

## Installation 
We use [Brownie](https://eth-brownie.readthedocs.io) to help in compiling, deploying, testing, and debugging. It's not needed for *using* ocean-lib-py.

[Install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

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

BTW, here's how to deactivate the env't at the end of a session:
```console
deactivate
```

## 1. Copy contracts
Outcome: the .sol files from other repos are in a freshly-created `contracts/` subdirectory here.

Set up env't, ensure it's up to date:
```console
source myenv/bin/activate
pip install -r requirements.txt 
source  ~/.ocean_vars
```

Create new directory, copy .sol files from other repos, and alter as needed:
```console
./copy_contracts.py
```

## 2. Compile the contracts 
Outcome: ABIs, from .sol files.

Get Brownie to look in `contracts/` and perform its magic:
```console
brownie compile
```

## 3. Deploy the contracts
Outcome: ERC20Template and Factory are deployed. 

First, ensure that envvars OPF_PRIVATE_KEY and OCEAN_COMMUNITY_ADDRESS are set. Typically, update `~/.ocean_vars`, then:
```console
source ~/.ocean_vars
```

Then, call the deploy script. Do this for each target NETWORK: ganache (`development`), `rinkeby`, or `mainnet`:
```console
./deploy.py NETWORK
```

## 4. Test ocean-lib-py
Outcome: ocean-lib-py works as expected on ganache, rinkeby, and mainnet.

Start by testing simple quickstart locally:
```console
pytest tests/test_quickstart_simpleflow.py
```

Then test everything:
```console
pytest
```

## 5. Debugging
Brownie reduces pain in Solidity debugging: it makes it feel like Python debugging, including Python-style tracebacks in Solidity. [Here's a walk-through](https://medium.com/better-programming/getting-started-with-brownie-part-3-ef6bfa9867d7) of key features. [Here are Brownie docs](https://eth-brownie.readthedocs.io). 

Lets's do some stuff with it. First, start the console.
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

