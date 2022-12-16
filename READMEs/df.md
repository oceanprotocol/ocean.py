# Quickstart: Data Farming Flow

This README shows how to do steps in Ocean Data Farming (DF), where you curate data assets to earn rewards. It also helps to democratize "wash consume" until it becomes unprofitable.

Here are the steps:

1. Setup, in Ganache
2. Lock OCEAN for veOCEAN
3. Publish dataset & exchange
4. Allocate veOCEAN to dataset
5. Fake-consume data
6. Collect OCEAN rewards
7. Repeat steps 1-6, for Eth mainnet

Let's go through each step.

## 1. Setup

### 1.1 Setup from console

From [installation-flow](install.md), do "Setup" section.

We also need to set the factory envvar. In the console:
```console
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

### 2.2 Setup in Python

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do "Setup in Python" section. 

Now, we're in the Python console.

### 2.3 Fake OCEAN

Alice needs (fake) OCEAN for later. In the same Python console:
```python
# mint OCEAN. Alice will get some
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

# simpler variable names
OCEAN = ocean.OCEAN_token
veOCEAN = ocean.ve_ocean
alice = alice_wallet
```

## 2. Lock OCEAN for veOCEAN

First, let's set some key parameters for veOCEAN and DF. On Ganache, you can use these values as-is. But on Eth mainnet, you must choose your own. In the same Python console:
```python
# On your asset, your DCV = DT_price * num_consumes
# Your asset gets rewards pro-rata for its DCV compared to other assets' DCVs. 
DT_price = 100.0 # number of OCEAN needed to buy one datatoken
num_consumes = 3

# This is how much OCEAN to lock into veOCEAN. It can be small if you're
# the only staker on your asset. If others stake on your asset, your
# rewards are pro-rate compared to others' stake in your asset.
amt_OCEAN_lock = 10.0
```

Now, let's lock OCEAN for veOCEAN. In the same Python console:
```python
#simulate passage of time, until next Thursday, the start of DF(X)
from brownie.network import chain
WEEK = 7 * 86400 # seconds in a week
t0 = chain.time()
t1 = t0 // WEEK * WEEK + WEEK #this is a Thursday, because Jan 1 1970 was
t2 = t1 + WEEK
chain.sleep(t1 - t0) 
chain.mine()

#we're now at the beginning of the week. So, lock
from ocean_lib.ocean.util import to_wei, from_wei
OCEAN.approve(veOCEAN.address, to_wei(amt_OCEAN_lock), {"from" : alice})
veOCEAN.withdraw({"from": alice}) #withdraw old tokens first
veOCEAN.create_lock(to_wei(amt_OCEAN_lock), t2, {"from": alice})
```


## 3. Publish Dataset & Exchange

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_NFT, DT, ddo) = ocean.assets.create_url_asset(name, url, alice, wait_for_aqua=False)
print(f"Just published asset, with data_NFT.address={data_NFT.address}")

#create exchange
exchange = DT.create_exchange(
    to_wei(DT_price), OCEAN.address, {"from": alice}
)

#make datatokens available on the exchange
DT.mint(alice, to_wei(num_consumes), {"from": alice})
DT.approve(exchange.address, to_wei(num_consumes), {"from": alice})
```


## 4. Stake on dataset

To stake, you allocate veOCEAN to dataset. In the same Python console:
```python
amt_allocate = 100 #total allocation must be <= 10000 (wei)
ocean.ve_allocate.setAllocation(amt_allocate, data_NFT.address, chain.id, {"from": alice})
```

## 5. Fake-consume data

"Wash consuming" is when the publisher fake-consumes data to drive data consume volume (DCV) to get more rewards. Not healthy for the ecosystem long-term. Good news: if consume fee > weekly rewards, then wash consume becomes unprofitable. DF is set up to make this happen by DF29 (if not sooner). [Details](https://twitter.com/trentmc0/status/1587527525529358336).

In the meantime, this README helps level the playing field around wash consume. This step shows how to do fake-consume.

```python
# Alice buys datatokens from herself
OCEAN_pay = DT_price * num_consumes
OCEAN_alice = from_wei(OCEAN.balanceOf(alice))
assert OCEAN_alice >= OCEAN_pay, f"Have just {OCEAN_alice} OCEAN"

OCEAN.approve(exchange.address, to_wei(OCEAN_alice), {"from": alice})
exchange.buy_DT(to_wei(num_consumes), {"from": alice})

DT_bal = from_wei(DT.balanceOf(alice))
assert DT_bal >= num_consumes, \
    f"Have {DT_bal} datatokens, too few for {num_consumes} consumes"

# Alice sends datatokens to the service, to get access. This is the "consume".
for i in range(num_consumes):
    print(f"Consume #{i+1}/{num_consumes}...")
    ocean.assets.pay_for_access_service(ddo, alice)
    #don't need to call e.g. ocean.assets.download_asset() since wash-consuming
```

## 6. Collect OCEAN rewards

In the same Python console:

```python
#simulate passage of time, until next Thursday, which is the start of DF(X+1)
WEEK = 7 * 86400 # seconds in a week
t0 = chain.time()
t1 = t0 // WEEK * WEEK + WEEK
t2 = t1 + WEEK
chain.sleep(t1 - t0) 
chain.mine()

#Rewards can be claimed via code or webapp, at your leisure. Let's do it now.
OCEAN_before = from_wei(OCEAN.balanceOf(alice))
ocean.ve_fee_distributor.claim({"from": alice})
OCEAN_after = from_wei(OCEAN.balanceOf(alice))
print(f"Just claimed {OCEAN_after - OCEAN_before} OCEAN rewards") 
```

## 7. Repeat steps 1-6, for Eth mainnet

We leave this as an exercise to the reader:)

Here's a hint to get started: initial setup is like the [simple-remote flow](simple-remote.md).

Happy Data Farming!

