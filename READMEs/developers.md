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

Initialize virtual env't. Activate env't.(BTW use `deactivate` to, well, deactivate.)
```console
python -m venv venv
source venv/bin/activate 
```

Install modules in the env't.
```
pip install -r requirements_dev.txt 
```

If you don't have an Infura account and you aim to deploy to `rinkeby`, go to www.infura.io and sign up.

## 2. Start blockchain service (ganache only)

Outcome: ganache running as a live blockchain network service, just like rinkeby.

Open a separate terminal and run ganache-cli (using docker)
```console
docker run -d -p 8545:8545 trufflesuite/ganache-cli:latest --mnemonic "taxi music thumb unique chat sand crew more leg another off lamp"
```

The comand above starts `ganache-cli` with accounts derived from that `mnemonic` seed phrase. 
You can see 10 accounts including addresses and private keys in the console. Use one of those 
accounts for doing on-chain transactions. 

For example, here's the first account from the ganache run: 
- address=0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
-  privateKey=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

## 3. Deploy the contracts

First, set envvars (since we don't want private keys on GitHub):
```console
export CONFIG_FILE=config.ini
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export ARTIFACTS_PATH=artifacts
```

If you already have contracts deployed to the network, then:
- Check that `artifacts/address.json` holds the up-to-date addresses for your target network.

If you don't yet have contracts deployed, then:
- Call: `./deploy.py NETWORK` where NETWORK = `ganache` or `rinkeby`. 
- This will deploy DataTokenTemplate, DTFactory, BFactory, etc to NETWORK
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
