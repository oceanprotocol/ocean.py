# Developing ocean-lib-py

This README is how to further *develop* ocean-lib-py. (Compare to the quickstarts which show how to *use* ocean-lib-py.)

Here, you can:
1. **Copy & compile contracts**: copy .sol from other repos, tweak imports, compile into ABIs etc
1. **Deploy** the contracts to {local, rinkeby, mainnet}
1. **Test** ocean-lib-py
1. (Along the way) **Debug** at the contract or py level.

These steps are detailed below. But first, installation. 

## 0. Installation 
We use [Brownie](https://eth-brownie.readthedocs.io) to help in compiling, deploying, testing, and debugging. It's not needed for *using* ocean-lib-py.

[Install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

Clone this repo, and `cd` into it.
```console
git clone https://github.com/oceanprotocol/ocean-lib-py
cd ocean-lib-py
```

Initalize virtual env't. Activate env't. Update modules in env't. (BTW use `deactivate` to, well, deactivate.)
```console
python -m venv myenv
source myenv/bin/activate 
pip install -r requirements.txt 
```

If you don't have an Infura account and you aim to deploy to `rinkeby` or `mainnet`, go to www.infura.io and sign up.

Private keys etc can't live on GitHub. To handle this, ocean-lib-py tools read ~/ocean.conf. (It does *not* use environmental variables.)

First, start with the pre-set template:
```console
cp sample_ocean.conf ~/ocean.conf
```

Then open `~/ocean.conf` and update the values as needed. This may include the infura id.

## 1. Copy & compile contracts
Outcomes: 
- `.sol` files from other repos in a freshly-created `contracts/` subdirectory with imports tweaked as needed.
- `.abi` files, compiled from the `.sol` with brownie
- ready for easy debugging via `brownie console`

Let's do it! 

Set up env't, ensure it's up to date:
```console
source myenv/bin/activate
pip install -r requirements.txt 
```

The run make! It git clones ,copies, tweaks imports, and finally does a `brownie compile`.
```console
./make.py
```

## 2. Deploy the contracts
Outcome: ERC20Template and Factory are deployed to ganache, rinkeby, or mainnet.

If mainnet: ensure `~/ocean.conf` has correct `FACTORY_DEPLOYER_PRIVATE_KEY` (= an OPF key) and `FEE_MANAGER_ADDRESS` (= Ocean community address).

If ganache: open a separate terminal, set the env't, and run the ganache script. 
- `cd <this dir>`
- `source myenv/bin/activate`
- `./ganache.py`

The ganache script has added `ganache` as a network to brownie (if needed), then started `ganache-cli` and pre-populate ETH into the private keys set in `~/ocean.conf`.

Call the deploy script with NETWORK = `ganache`, `rinkeby`, or `mainnet`. Brownie will attach to the network.
```console
./deploy.py NETWORK
```

Finally: update `ocean.conf`'s `FACTORY_ADDRESS` with the factory address output in the previous step.

## 3. Test ocean-lib-py
Outcome: ocean-lib-py works as expected.

First, ensure that ganache-cli is running like in step 2: `ganache-cli --port ...`.

Then, test simple quickstart on it:
```console
pytest tests/test_quickstart_simpleflow.py::test_on_ganache
```

Then, test simple quickstart on the other networks:
```console
pytest tests/test_quickstart_simpleflow.py::test_on_rinkeby
pytest tests/test_quickstart_simpleflow.py::test_on_mainnet
```

Then, test everything:
```console
pytest
```

## 4. Debugging
Brownie reduces pain in Solidity debugging: it makes it feel like Python debugging, including Python-style tracebacks in Solidity. [Here's a walk-through](https://medium.com/better-programming/getting-started-with-brownie-part-3-ef6bfa9867d7) of key features. [Here are Brownie docs](https://eth-brownie.readthedocs.io). 

Lets's do some stuff with it. First, start the console.
```bash
brownie console
```

Play in brownie console! Here's an end-to-end example that deploys a factory (and token template), creates a token, then retreives the token address:
```python
>>> ERC20_template = DataTokenTemplate.deploy("Template","TEMPLATE", factory_deployer_account.address, 1000, "blob", factory_deployer_account.address, {'from':factory_deployer_account
})                                                                                                                                                                                     
Transaction sent: 0xc17f63a24aac9e906ee7847f8a21c13f00e937a6e0ad1eebf32b412f347f380b
  Gas price: 0.0 gwei   Gas limit: 6721975
  DataTokenTemplate.constructor confirmed - Block: 1   Gas used: 1616110 (24.04%)
  DataTokenTemplate deployed at: 0xE7b2aEceba7367057287980187A0477D8012C4F9

>>> factory = Factory.deploy(ERC20_template.address, factory_deployer_account.address, {'from':factory_deployer_account})                                                              
Transaction sent: 0x9785143287fb92add792923478946b299701d2bce9a6074fbe7e1d0a1b77bd93
  Gas price: 0.0 gwei   Gas limit: 6721975
  Factory.constructor confirmed - Block: 2   Gas used: 692655 (10.30%)
  Factory deployed at: 0x6a7eaF9c068C9742646C121e66625aeeE1CE6A02

>>> factory.createToken("Test Token", "TST", 1000, "test blob", accounts[0].address, {'from':accounts[0]})                                                                             
Transaction sent: 0x09ad403c6aa481596de03c5a9d662ab46799154a0f857c8b09d5efd3bc4f06bf
  Gas price: 0.0 gwei   Gas limit: 6721975
  Factory.createToken confirmed - Block: 3   Gas used: 254228 (3.78%)

<Transaction '0x09ad403c6aa481596de03c5a9d662ab46799154a0f857c8b09d5efd3bc4f06bf'>
>>> factory.getTokenAddress("TST")                                                                                                                                                     
'0x9f5C0E5080890F00Cf7Df7AD1D112503d1bf6c14'
```

