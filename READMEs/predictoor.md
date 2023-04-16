# Quickstart: Predictoor

This README currently describes how to **develop** Predictoor prototype.

When Predictoor is more mature, this README will change to _using_ Predictoor.

## 1. Install dependencies

### Prerequisites

-   Linux/MacOS
-   Docker, [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

### Do Install

In a new console that we'll call the _work_ console (as we'll use it later):

```console
# Clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py

# Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

# Initialize virtual environment and activate it.
# Make sure your Python version inside the venv is >=3.8.
python3 -m venv venv
source venv/bin/activate

# Install modules in the environment.
pip install -r requirements_dev.txt
```

## 2. Run barge

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache; deploy contracts; add fake OCEAN; update ~/.ocean
# - It's barebones, since Aquarius, Provider, etc aren't needed. Runs _way_ after:)
./start_ocean.sh --no-aquarius --no-elasticsearch --no-provider --no-ipfs --no-dashboard --skip-subgraph-deploy
```

**FIXME: we actually need custom contracts deployed. See the [contracts repo "Development and Testing" section](https://github.com/oceanprotocol/contracts#-development-and-testing)**.


## 3. Set up envvars for contracts

In work console:

```console
#set private keys of two local (ganache) accounts
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

#needed to mint fake OCEAN for testing with ganache
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

If you are runing remote tests, you'll also need:
```console
#set private keys of two remote accounts
export REMOTE_TEST_PRIVATE_KEY1=<your remote private key 1>
export REMOTE_TEST_PRIVATE_KEY2=<your remote private key 2>
```

These keys aren't public because bots could eat the fake MATIC. You need to generate your own, and fill them with a faucet; see instructions in remote setup README. Or, [access-protected OPF keys](https://github.com/oceanprotocol/private-keys/blob/main/README.md).

## 4. Test

In work console:
```console
#run main prototype 3 test. The "-s" gives verbose printing.
pytest ocean_lib/models/test/test_datatoken3.py  -s
```

For envvars that aren't set, `pytest` uses values in `pytest.ini`.
