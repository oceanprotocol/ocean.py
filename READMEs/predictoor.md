# Quickstart: Predictoor

This README currently describes how to **develop** Predictoor prototype.

When Predictoor is more mature, this README will change to _using_ Predictoor.

## 1. Pre-Requisites

Ensure pre-requisites:

- Linux/MacOS
- Python 3.8.5+


## 2. Start barge

Open a new console, call it "barge console".

If you don't have barge:

```console
git clone https://github.com/oceanprotocol/barge
cd barge
```

Since ocean-contracts predictoor branch is WIP, make sure you always pull latest version before running barge

```console
docker pull oceanprotocol/ocean-contracts:predictoor 
export CONTRACTS_VERSION: predictoor
./start_ocean.sh --predictoor
```


## 3. Install

Open a new console, call it "work console".

In work console:

```console
# Clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py
git checkout predictoor-with-barge

# Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

#create a virtual environment
python -m venv venv

#activate env
source venv/bin/activate

#install dependencies
pip install -r requirements_dev.txt

```

## 4. Set envvars in work console

While we already set these envvars in the ganache console, let's also get them in our work console. In work console:

```console
#set private keys
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc
export TEST_PRIVATE_KEY3=0xed45162e5e39ecdd5270afdef42eba06a67dd455b6e580cbeefc1c7de31ee4e2
export TEST_PRIVATE_KEY4=0x9dae18de1b391af0dad691e0566104aedbaf71855ec056feb7567065270a7fd3
export TEST_PRIVATE_KEY5=0xbe8b3fe8699d05bee83f2522ca24f71900356519936c4dd45a8ca8aa1c0f7f35
export TEST_PRIVATE_KEY6=0x3ff9bd14c137a8d1eec9980046c0fefde79c5ac2b023b20bed34363246b94b09
```

## 5. Test

In work console:
```console
#run main prototype 3 test. The "-s" gives verbose printing.
pytest ocean_lib/models/test/test_datatoken3.py::test_main  -s
```

For envvars that aren't set, `pytest` uses values in `pytest.ini`.
