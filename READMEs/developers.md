# Developing ocean-lib-py

This README is how to further *develop* ocean-lib-py. (Compare to the quickstarts which show how to *use* it.)

Steps:
1. **Install dependencies**
1. **Start blockchain service** (only needed for ganache)
1. **Copy & compile contracts**: copy .sol from other repos, tweak imports, compile into ABIs etc
1. **Deploy** the contracts to {local, rinkeby, mainnet}
1. **Test** 
1. (Along the way) **Debug** at the contract or py level.

These steps are detailed below. But first, installation. 

## 1. Install dependencies 

Clone this repo, and `cd` into it.
```console
git clone https://github.com/oceanprotocol/ocean-lib-py
cd ocean-lib-py
```

Initalize virtual env't. Activate env't.(BTW use `deactivate` to, well, deactivate.)
```console
python -m venv myenv
source myenv/bin/activate 
```

Install modules in the env't. Notably, it installs [Brownie](https://eth-brownie.readthedocs.io). Brownie helps in compiling, deploying, testing, and debugging. Brownie is not needed for *using* ocean-lib-py.
```
pip install -r requirements.txt 
```

If you don't have an Infura account and you aim to deploy to `rinkeby` or `mainnet`, go to www.infura.io and sign up.

Private keys etc can't live on GitHub. To handle this, ocean-lib-py tools read ~/ocean.conf. (It does *not* use environmental variables.) Start with the pre-set template:
```console
cp sample_ocean.conf ~/ocean.conf
```

Then open `~/ocean.conf` and update the values as needed. This may include the infura id.

## 2. Start blockchain service (ganache only)

Outcome: ganache running as a live blockchain network service, just like mainnet and rinkeby.

Open a separate terminal and set the env't. and run the ganache script. 
```console
cd <this dir>`
source myenv/bin/activate
```

Run the ganache script. It adds `ganache` as a network to brownie (if needed), then starts `ganache-cli` including putting ETH into the private keys set in `~/ocean.conf`.
```console
./ganache.py
```

## 3. Copy & compile contracts

Outcomes: 
- a freshly-created `oceanbrownie/` project directory. 
- `.sol` files from other repos in `oceanbrownie/contracts/` with imports tweaked as needed.
- `.abi` files, compiled from the `.sol` with brownie
- ready for easy debugging via `brownie console`

Let's do it! 

Set up env't, ensure it's up to date:
```console
source myenv/bin/activate
pip install -r requirements.txt 
```

For the next step, you may need more than the pip-installed brownie pip from step 1. If you do: here's [how to install Brownie](https://medium.com/@iamdefinitelyahuman/getting-started-with-brownie-part-1-9b2181f4cb99). It can be tricky; [here's steps](https://github.com/trentmc/brownie-instrs/blob/master/README_install.md) that I followed.

The run make! It git clones ,copies, tweaks imports, and finally does a `brownie compile`.
```console
./make.py
```

## 4. Deploy the contracts
Outcome: ERC20Template and Factory are deployed to ganache, rinkeby, or mainnet.

If mainnet: ensure `~/ocean.conf` has correct `FACTORY_DEPLOYER_PRIVATE_KEY` (= an OPF key) and `FEE_MANAGER_ADDRESS` (= Ocean community address).

Call the deploy script with NETWORK = `ganache`, `rinkeby`, or `mainnet`. Brownie will attach to the network.
```console
./deploy.py NETWORK
```

Finally: update `ocean.conf`'s `FACTORY_ADDRESS` with the factory address output in the previous step.

## 5. Test 
Outcome: ocean-lib-py works as expected.

First, run simple quickstart on ganache. 
```console
./quickstart_simpleflow.py ganache
```

And repeat on rinkeby etc.

## 6a. (Optional) Brownie Debugging, Directly on Solidity Objects

Brownie reduces pain in Solidity debugging: it makes it feel like Python debugging, including Python-style tracebacks in Solidity. [Here's a walk-through](https://medium.com/better-programming/getting-started-with-brownie-part-3-ef6bfa9867d7) of key features. [Here are Brownie docs](https://eth-brownie.readthedocs.io). 

Lets's do some stuff with Brownie. First, start the console. We specify the network so it doesn't default to 'development'.
```bash
brownie console --network ganache
```

Play in brownie console! Here's an end-to-end example that deploys a factory (and token template), creates a token, then retreives the token address:
```python

>>> factory_deployer_account = network.accounts.add(private_key='0x904365e293b9fab9bd11bddd39082396d56d30779efbb3ffb0a6089027902c4a')

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
>>> token_address = factory.getTokenAddress("TST")
'0x9f5C0E5080890F00Cf7Df7AD1D112503d1bf6c14'

```

## 6b. (Optional) Brownie Debugging, using Ocean.py libraries

Above, we used Brownie to directly deploy .sol-derived objects. Here, we go through the Ocean interface but still draw on Brownie's traceback abilities.

First:
```bash
brownie console --network ganache
```

Then inside brownie:
```python

#copy and paste the following to >>>
import brownie #not needed, but clarifies the usage of brownie modules
from ocean_lib import Ocean
network_str = 'ganache' 

alice_private_key = Ocean.confFileValue(network_str, 'TEST_PRIVATE_KEY1')
bob_private_key = Ocean.confFileValue(network_str, 'TEST_PRIVATE_KEY2')
bob_address = Ocean.privateKeyToAddress(bob_private_key)

config = {'network' : network_str, 'privateKey' : alice_private_key}
ocean = Ocean.Ocean(config)
token = ocean.createToken('localhost:8030')
dt_address = token.getAddress()
print(dt_address)
```

So far so good. Let's keep going.
```python
token.mint(100)

token.transfer(bob_address, 1)

bob_config = {'network' : network_str, 'privateKey' : bob_private_key}
bob_ocean = Ocean.Ocean(bob_config)
token = bob_ocean.getToken(dt_address)
_file = token.download()
```

We can also combine objects from 6a, for richer debugging. For example:
```python
factory_deployer_account = network.accounts.add(private_key='0x904365e293b9fab9bd11bddd39082396d56d30779efbb3ffb0a6089027902c4a')

brownie_datatoken = DataTokenTemplate.deploy("Template2","TEMPLATE2", factory_deployer_account.address, 1000, "blob", factory_deployer_account.address, {'from' : factory_deployer_account}) 
brownie_datatoken.mint(factory_deployer_account.address, 10, {'from': factory_deployer_account, 'value':100000000000})
```
