# Quickstart: Predictoor

This README currently describes how to **develop** Predictoor prototype.

When Predictoor is more mature, this README will change to _using_ Predictoor.

## 1. Pre-Requisites

Ensure pre-requisites:

- Linux/MacOS
- Python 3.8.5+
- solc 0.8.0+ [[Instructions](https://docs.soliditylang.org/en/v0.8.9/installing-solidity.html)]
- ganache. [To install](https://github.com/trufflesuite/ganache#readme): `npm install ganache --global`

## 2. Start ganache, fund accounts

Open a new console and:

```console
#set private keys
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

#each account gets 1000 ETH
export AMT_ETH=1000000000000000000000

#start ganache
ganache --account "$FACTORY_DEPLOYER_PRIVATE_KEY,$AMT_ETH" --account "$TEST_PRIVATE_KEY1,$AMT_ETH" --account "$TEST_PRIVATE_KEY2,$AMT_ETH" 
```

## 3. Install

Open a new console, call it "work console".

In work console:

```console
# Clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py
git checkout predictoor-pm-issue-3

# Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

#create a virtual environment
python -m venv venv

#activate env
source venv/bin/activate

#install dependencies
pip install -r requirements_dev.txt

#install openzeppelin library, to import from .sol (ignore FileExistsErrors)
brownie pm install OpenZeppelin/openzeppelin-contracts@4.2.0
brownie pm install GNSPS/solidity-bytes-utils@0.8.0

## 4. Set envvars in work console

While we already set these envvars in the ganache console, let's also get them in our work console. In work console:

```console
#set private keys
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc
```

## 5. Compile & deploy contracts

We need to compile once at the beginning, and recompile whenever we change ERC20Template3.sol.

In work console:
```console
#remove old build artifacts
rm -rf build

#compile contracts
brownie compile

#deploy contracts to ganache
./deploy.py
```

## 6. Test

In work console:
```console
#run main prototype 3 test. The "-s" gives verbose printing.
pytest ocean_lib/models/predictoor/test/test_datatoken3.py  -s
```

For envvars that aren't set, `pytest` uses values in `pytest.ini`.
