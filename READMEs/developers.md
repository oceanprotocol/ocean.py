# Developing ocean.py

This README is how to further *develop* ocean.py. (Compare to the quickstarts which show how to *use* it.)
Steps:
1. **Install dependencies**
1. **Configure the services**
1. **Test**
1. **Merge** the changes via a PR
1. **Release** 

## Prerequisites

1. Linux/MacOS
2. Docker
3. Python 3.8.5

## 1. Install dependencies

Clone this repo, and `cd` into it.
```console
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py
```
Install OS dependencies (e.g. Linux)
```console
sudo apt-get install -y python3-dev gcc python-pytest
```

Initialize virtual environment and activate it.
```console
python -m venv venv
source venv/bin/activate
```

Install modules in the environment.
```
pip install -r requirements_dev.txt
```


## 2. Start network, deploy to network (Local only)
To use Ocean.py, following services should be running: Aquarius, Ethereum node with contracts, Provider.
You can run `barge` to start all the required services or run each component individually.  

### Option 1: Use Barge (recommended)
To start all required services: ganache, provider, aquarius and deploy the contracts, do this in a separate terminal:
```console
git clone https://github.com/oceanprotocol/barge
cd barge
./start_ocean.sh
```

### Option 2: Run each component separately

1. Start ganache: Open a new terminal. In it, start a local ganache network with the following mnemomic. (The tests need private keys from this mnemomic.)
```console
docker run -d -p 8545:8545 trufflesuite/ganache-cli:latest --mnemonic "taxi music thumb unique chat sand crew more leg another off lamp"
```

2. Open another new terminal. In it:
* Clone the [Ocean contracts repo](https://github.com/oceanprotocol/contracts): `git clone https://github.com/oceanprotocol/contracts`
* Go to the new repo directory: `cd contracts`
* Deploy to the local network: `npm run deploy`

These steps will have updated the file `artifacts/address.json` in the _contracts_ directory, in the `development` section.

3. Start [aquarius](https://github.com/oceanprotocol/aquarius/blob/master/README.md)
4. Start [provider](https://github.com/oceanprotocol/provider)

## 3. Set contract addresses
1. If using barge, the generated addresses will be available at path `~/.ocean/ocean-contracts/artifacts/address.json`.
Copy the values from that section the into your local _ocean.py_'s artifacts file, e.g. at `./ocean.py/artifacts/address.json`. The result should look something like:
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
2. Deploy fake OCEAN:
* In terminal: `./deploy.py ganache`
* It will output the address of OCEAN. Update the `artifacts/address.json` file with that address.


Similarly. the deployed contracts on other networks can be found [here](https://github.com/oceanprotocol/contracts/blob/master/artifacts/address.json).


## 4. Connect to the deployed contracts (Local or Rinkeby)

Open `./config.ini` and check that these lines exist (under `[eth-network]`):
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
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209
```

Some tests don't need other services running. Let's run one:
```console
pytest tests/models/test_btoken.py
```

Now you can run all tests since all services are running:
```console
pytest
```

#### Installing the pre-commit hooks (recommended)
Run `pre-commit install` to automatically apply isort (import sorting), flake8 (linting) and black (automatic code formatting) to commits. Black formatting is the standard and is checked as part of pull requests.

## 5. Merge

Merge the changes via a pull request (PR) etc. 

Specifically, [follow this workflow](https://docs.oceanprotocol.com/concepts/contributing/#fix-or-improve-core-software).

## 6. Release

Release for pip etc.

Specifically, [follow the Release Process instructions](../RELEASE_PROCESS.md).
