# Developing ocean.py

This README is how to further *develop* ocean.py. (Compare to the quickstarts which show how to *use* it.)

Steps:
1. **Install dependencies**
1. **Start blockchain service** (only needed for ganache)
1. **Deploy** the contracts to {local, rinkeby, mainnet}
1. **Test** 

These steps are detailed below. But first, installation. 

## 1. Install dependencies 

Clone this repo, and `cd` into it.
```console
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py
```

Initialize virtual env't. Activate env't. (BTW use `deactivate` to, well, deactivate.)
```console
python -m venv venv
source venv/bin/activate 
```

Install modules in the env't.
```
pip install -r requirements_dev.txt 
```

If you don't have an Infura account and you aim to deploy to `rinkeby`, go to www.infura.io and sign up.

## 2. Start network, deploy to network (Local only) 

Follow the directions in [Ocean contracts repo](https://github.com/oceanprotocol/contracts) to:
* Clone the repo locally, e.g. to `./contracts`
* Start a local ganache network
* Deploy to it

These steps will have updated the file `artifacts/address.json` in the _contracts_ directory, in the `development` section. 

As a final step: copy the values from that section the into your local _ocean.py_'s artifacts file, e.g. at `./ocean.py/artifacts/address.json`. The result should look something like:
```
{"Rinkeby":  {
    "DTFactory": "0x3fd7A00106038Fb5c802c6d63fa7147Fe429E83a",
    ...
},
 "development": {
    "DTFactory": "0xC36D83c8b8E31D7dBe47f7f887BF1C567ff75DD7",
    "BFactory": "0x5FcC55C678FEad140487959bB73a3f3B6949DdE5",
    "FixedRateExchange": "0x143027A9705e4Fe24734D99c7458aBe5A6b38D8e",
    "Metadata": "0xdA00aD9ae0ABD347eaFCbFCe078bEFCB30eD59cD",
    "Ocean": "0x83c74A95e42244CA84DbEB01C5Bfd5b2Cd2691c2"
 }
}
```

## 3. Connect to the deployed contracts (Local or Rinkeby)

First, set envvars (since we don't want private keys on GitHub):
```console
export CONFIG_FILE=config.ini
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export ARTIFACTS_PATH=artifacts
```

If you already have contracts deployed to the network, then:
- Double-check that `artifacts/address.json` holds the up-to-date addresses for your target network.

If you don't yet have contracts deployed, then:
- Call: `./deploy.py NETWORK` where NETWORK = `ganache` or `rinkeby`. 
- Double-check that it updated the file `artifacts/address.json` with the addresses

Finally, open `./config.ini` file, and make sure there's a line to set address.file: `address.file = artifacts/address.json`.

## 4. Test 
Outcome: ocean.py works as expected.

Some tests don't need other services running. Let's run one:
```console
pytest tests/bpool/test_btoken.py
```

Some tests need an Ocean Provider running. Follow 
[these steps](https://github.com/oceanprotocol/provider-py/blob/master/README.md) 
to set up Provider. Then run test(s) that use Provider (but not other services). 
For example:
```console
pytest tests/ocean/test_market_flow.py
```

Some tests need an Ocean Provider *and* Aquarius (database service) running. Follow 
[these steps](https://github.com/oceanprotocol/aquarius) to set up Aquarius. Then run 
test(s) that use Provider and Aquarius. For example:
```console
pytest 
```

Alternatively, you can run `barge` to start all required services: ganache, provider, 
aquarius and deploy the contracts. To start `barge` do this in a separate terminal:
```console
git clone https://github.com/oceanprotocol/barge
cd barge
git checkout v3
bash -x start_ocean.sh 2>&1 > start_ocean.log &

```

Now you can run all tests since all services are running:
```console
pytest
```
