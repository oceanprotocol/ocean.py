# Developing ocean-lib-py

This README is how to further *develop* ocean-lib-py. (Compare to the quickstarts which show how to *use* it.)

Steps:
1. **Install dependencies**
1. **Start blockchain service** (only needed for ganache)
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
python -m venv venv
source venv/bin/activate 
```

Install modules in the env't.
```
pip install -r requirements_dev.txt 
```

If you don't have an Infura account and you aim to deploy to `rinkeby` or `mainnet`, go to www.infura.io and sign up.

Private keys etc can't live on GitHub. To handle this, ocean-lib-py tools read from environment variables:
```console
    
```

Then open `~/ocean.conf` and update the values as needed. This may include the infura id.

## 2. Start blockchain service (ganache only)

Outcome: ganache running as a live blockchain network service, just like mainnet and rinkeby.

Open a separate terminal and set the env't. and run the ganache script. 
```console
cd <this dir>`
source venv/bin/activate
```

Run the ganache script. It starts `ganache-cli` including putting ETH into the private keys set in the environment
```console
./ganache.py
```

## 3. Deploy the contracts
Outcome: DataTokenTemplate and DTFactory are deployed to ganache, rinkeby, or mainnet.

If mainnet: ensure the `FACTORY_DEPLOYER_PRIVATE_KEY` is correct (= an OPF key).

Call the deploy script with (NETWORK = `ganache`, `rinkeby`, or `mainnet`) and (ADDRESSES_FILE_PATH to hold the deployed contracts addresses). 
When using already deployed contracts you can skip this, but make sure the `artifacts/address.json` file has the up-to-date contracts 
addresses for the target network.
```console
./deploy.py ganache artifacts/address.json
```

Finally: update `config.ini`'s `address.file` with the ADDRESSES_FILE_PATH from the previous step.

## 4. Test 
Outcome: ocean-lib-py works as expected.

Some tests don't need other services running. Let's run one:
```console
pytest tests/bpool/test_BToken.py
```

Some tests need an Ocean Provider running. Follow [these steps](https://github.com/oceanprotocol/provider-py/blob/master/README.md) to set up Provider. Then run test(s) that uses Provider (but not other services). For example:
```console
pytest tests/ocean/test_simple_flow.py
```

Some tests need an Ocean Provider *and* Aquarius (database service) running. Follow [these steps](https://github.com/oceanprotocol/aquarius) to set up Aquarius. Then run test(s) that use Provider and Aquarius. For example:
```console
pytest 
```

And repeat on rinkeby etc.

## 5a. (Optional) Brownie Debugging, Directly on Solidity Objects

Brownie reduces pain in Solidity debugging: it makes it feel like Python debugging, including Python-style tracebacks in Solidity. [Here's a walk-through](https://medium.com/better-programming/getting-started-with-brownie-part-3-ef6bfa9867d7) of key features. [Here are Brownie docs](https://eth-brownie.readthedocs.io). 

COMING SOON ..


## 5b. (Optional) Brownie Debugging, using Ocean.py libraries

COMING SOON ..
