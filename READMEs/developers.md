# Developing ocean.py

This README is how to further *develop* ocean.py. (Compare to the quickstarts which show how to *use* it.)

Steps:
1. **Install dependencies**
1. **Start blockchain service** (only needed for ganache)
1. **Deploy** the contracts to {local, rinkeby, mainnet}
1. **Test**
1. **Release** 

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

Open a new terminal. In it, start a local ganache network with the following mnemomic. (The tests need private keys from this mnemomic.)
```console
docker run -d -p 8545:8545 trufflesuite/ganache-cli:latest --mnemonic "taxi music thumb unique chat sand crew more leg another off lamp"
```

Open another new terminal. In it:
* Clone the [Ocean contracts repo](https://github.com/oceanprotocol/contracts): `git clone https://github.com/oceanprotocol/contracts`
* Go to the new repo directory: `cd ocean.py`
* Deploy to the local network: `npm run deploy`

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

First, open `artifacts/address.json` and check that:
* does it have up-to-date addresses for your target network?

Then, open `./config.ini` and check that these lines exist (under `[eth-network]`):
* `address.file = artifacts/address.json`
* `artifacts.path = artifacts`

Finally, set envvars.
```console
export CONFIG_FILE=config.ini
```

## 4. Test

First, set private key values that the tests will need. The first key's value lines up with the ganache mnemomic setting above.
```console
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY2=0xaefd8bc8725c4b3d15fbe058d0f58f4d852e8caea2bf68e0f73acb1aeec19bab
```

If you're on ganache, then you also need to deploy fake OCEAN:
* In terminal: `./deploy.py ganache`
* It will output the address of OCEAN. Update the `artifacts/address.json` file with that address.

Some tests don't need other services running. Let's run one:
```console
pytest tests/models/bpool/test_btoken.py::test_notokens_basic
```

Some tests need an Ocean Provider running. Follow [these steps](https://github.com/oceanprotocol/provider-py/blob/master/README.md) to set up Provider. Then run tests that use Provider (but not other services). For example:
```console
pytest tests/ocean/test_market_flow.py
```

Some tests need an Ocean Provider *and* Aquarius (metadata cache) running. Follow [these steps](https://github.com/oceanprotocol/aquarius) to set up Aquarius. Then run tests that use Provider and Aquarius. For example:
```console
pytest
```

Alternatively, you can run `barge` to start all required services: ganache, provider, aquarius and deploy the contracts. To start `barge` do this in a separate terminal:
```console
git clone https://github.com/oceanprotocol/barge
cd barge
bash -x start_ocean.sh 2>&1 > start_ocean.log &
```

Now you can run all tests since all services are running:
```console
pytest
```

#### Installing the pre-commit hooks (recommended)
Run `pre-commit install` to automatically apply isort (import sorting), flake8 (linting) and black (automatic code formatting) to commits. Black formatting is the standard and is checked as part of pull requests.

## 5. Release

Release for pip etc using the [Release Process instructions](RELEASE_PROCESS.md).
