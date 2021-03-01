<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
# Developing ocean.py

This README is how to further *develop* ocean.py. (Compare to the quickstarts which show how to *use* it.)
Steps:
1. **Install dependencies**
1. **Run the services**
1. **Set up contracts**
1. **Test**
1. **Merge** the changes via a PR
1. **Release** 


## 1. Install dependencies

### 1.1 Prerequisites

* Linux/MacOS
* Docker
* Python 3.8.5

### 1.2 Do Install

In a console:
```console
#clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py

#Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install modules in the environment.
pip install -r requirements_dev.txt
```


## 2. Run the services

Use Ocean Barge to run local Ethereum node with Ocean contracts, Aquarius, and Provider.

In a new console:
```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

#run barge with provider on
./start_ocean.sh  --with-provider2 
```

(Or, [run services separately](services.md).)

## 3. Set up contracts

### 3.1 Update `address.json`

Running barge has written addresses to `~/.ocean/ocean-contracts/artifacts/address.json`. Copy those into your local ocean.py's file `artifacts/address.json`. The result should look something like:
```json
{
  "development": {
    "DTFactory": "0xC36D83c8b8E31D7dBe47f7f887BF1C567ff75DD7",
    "BFactory": "0x5FcC55C678FEad140487959bB73a3f3B6949DdE5",
    "FixedRateExchange": "0x143027A9705e4Fe24734D99c7458aBe5A6b38D8e",
    "Metadata": "0xdA00aD9ae0ABD347eaFCbFCe078bEFCB30eD59cD",
    "Ocean": "0x83c74A95e42244CA84DbEB01C5Bfd5b2Cd2691c2"
 } 
}
```

### 3.2 Set private keys

```console
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209
```

### 3.3 Deploy fake OCEAN

* In terminal: `./deploy.py ganache`
* It will output the address of OCEAN. In `artifacts/address.json`, update the "development" : "Ocean" value with that address.

### 3.4 Connect to the deployed contracts

Open `./config.ini` and check that these lines exist (under `[eth-network]`):
* `address.file = artifacts/address.json`
* `artifacts.path = artifacts`

Finally, set envvars.
```console
export CONFIG_FILE=config.ini
```


## 4. Test

```console
#run a single test
pytest tests/models/test_btoken.py

#run all tests
pytest
```

Bonus: see the [appendix](developers.md#7-appendix-more-tests) for even more tests.

## 5. Merge

Merge the changes via a pull request (PR) etc. 

Specifically, [follow this workflow](https://docs.oceanprotocol.com/concepts/contributing/#fix-or-improve-core-software).

## 6. Release

Release for pip etc.

Specifically, [follow the Release Process instructions](../RELEASE_PROCESS.md).

## 7. Appendix: More tests

### 7.1 Pre-commit hooks

In main console (with venv on):
```console
pre-commit install
```

Now, this will auto-apply isort (import sorting), flake8 (linting) and black (automatic code formatting) to commits. Black formatting is the standard and is checked as part of pull requests.

### 7.2 Code quality tests

Use [codacy-analysis-cli](https://github.com/codacy/codacy-analysis-cli).

First, install once. In a new console:
```console
curl -L https://github.com/codacy/codacy-analysis-cli/archive/master.tar.gz | tar xvz
cd codacy-analysis-cli-* && sudo make install
```

In main console (with venv on):
```console
#run all tools, plus Metrics and Clones data. 
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean

#run tools individually
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Pylint
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Prospector
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Bandit
```

You'll get a report that looks like this. 
```console
Found [Info] `First line should end with a period (D415)` in ocean_compute.py:50 (Prospector_pep257)
Found [Info] `Missing docstring in __init__ (D107)` in ocean_assets.py:42 (Prospector_pep257)
Found [Info] `Method could be a function` in ocean_pool.py:473 (PyLint_R0201)
Found [Warning] `Possible hardcoded password: ''` in ocean_exchange.py:23 (Bandit_B107)
Found [Metrics] in ocean_exchange.py:
  LOC - 68
  CLOC - 4
  #methods - 6
```

(C)LOC = (Commented) Lines Of Code.

Finally, you can [go here](https://app.codacy.com/gh/oceanprotocol/ocean.py/dashboard) to see results of remotely-run tests. (You may need special permissions.)
