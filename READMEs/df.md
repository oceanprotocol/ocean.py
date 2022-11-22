# Quickstart: Data Farming Flow

This README shows how to do steps in Ocean Data Farming (DF), where you curate data assets to earn rewards. It also helps to democratize "wash consume" until it becomes unprofitable.

Here are the steps:

1. Setup, in Ganache
2. Lock OCEAN for veOCEAN
3. Publish dataset & FRE
4. Allocate veOCEAN to dataset
5. Fake-consume data
6. Collect OCEAN rewards
7. Repeat steps 1-6, for Eth mainnet

Let's go through each step.

## 1. Setup

### 1.1 Basic setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python, including `ocean` and `alice_wallet`


### 1.2 Setup key parameters

In Ganache, you can use these parameters as-is. But on Eth mainnet, you need to choose these for yourself.

In the same Python console:
```python
# On your asset, your DCV = datatoken_price_OCEAN * num_consumes.
# Your asset gets rewards pro-rata for its DCV compared to other assets' DCVs. 
datatoken_price_OCEAN = 100.0
num_consumes = 3

# This is how much OCEAN to lock into veOCEAN. It can be small if you're
# the only staker on your asset. If others stake on your asset, your
# rewards are pro-rate compared to others' stake in your asset.
amt_OCEAN_lock = 10.0
```


### 1.3 Setup OCEAN and veOCEAN

We'll use these a lot. So import once, here. 
In the same Python console:
```python
# Set factory envvar. Stay in Python to retain state from before.
os.environ['FACTORY_DEPLOYER_PRIVATE_KEY'] = '0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58'
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config) #Alice gets some

OCEAN = ocean.OCEAN_token
veOCEAN = ocean.ve_ocean

#helper functions
def to_wei(amt_eth) -> int:
    return int(amt_eth * 1e18)

def from_wei(amt_wei: int) -> float:
    return float(amt_wei / 1e18)
```


## 2. Lock OCEAN for veOCEAN

In the same Python console:
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
OCEAN.approve(veOCEAN.address, to_wei(amt_OCEAN_lock), {"from" : alice_wallet})
veOCEAN.withdraw({"from": alice_wallet}) #withdraw old tokens first
veOCEAN.create_lock(to_wei(amt_OCEAN_lock), t2, {"from": alice_wallet})
```


## 3. Publish Dataset & FRE

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_NFT, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet, wait_for_aqua=False)
print(f"Just published asset, with data_NFT.address={data_NFT.address}")

# create fixed-rate exchange (FRE)
from web3 import Web3
exchange_id = ocean.create_fixed_rate(
    datatoken=datatoken,
    base_token=OCEAN,
    amount=Web3.toWei(num_consumes, "ether"),
    fixed_rate=Web3.toWei(datatoken_price_OCEAN, "ether"),
    from_wallet=alice_wallet,
)
```


## 4. Stake on dataset

To stake, you allocate veOCEAN to dataset. In the same Python console:
```python
amt_allocate = 100 #total allocation must be <= 10000 (wei)
ocean.ve_allocate.setAllocation(amt_allocate, data_NFT.address, chain.id, {"from": alice_wallet})
```

## 5. Fake-consume data

"Wash consuming" is when the publisher fake-consumes data to drive data consume volume (DCV) to get more rewards. Not healthy for the ecosystem long-term. Good news: if consume fee > weekly rewards, then wash consume becomes unprofitable. DF is set up to make this happen by DF29 (if not sooner). [Details](https://twitter.com/trentmc0/status/1587527525529358336).

In the meantime, this README helps level the playing field around wash consume. This step shows how to do fake-consume.

```python
# Alice buys datatokens from herself
amt_pay = datatoken_price_OCEAN * num_consumes
OCEAN_bal = from_wei(OCEAN.balanceOf(alice_wallet.address))
assert OCEAN_bal >= amt_pay, f"Have just {OCEAN_bal} OCEAN"
OCEAN.approve(ocean.fixed_rate_exchange.address, to_wei(OCEAN_bal), {"from": alice_wallet})
fees_info = ocean.fixed_rate_exchange.get_fees_info(exchange_id)
for i in range(num_consumes):
    print(f"Purchase #{i+1}/{num_consumes}...")
    txid = ocean.fixed_rate_exchange.buy_dt(
        exchange_id=exchange_id,
    	datatoken_amount=to_wei(num_consumes),
    	max_base_token_amount=to_wei(OCEAN_bal),
    	consume_market_swap_fee_address=fees_info[1],
    	consume_market_swap_fee_amount=fees_info[0],
    	from_wallet=alice_wallet,
    )
    assert txid, "buying datatokens failed"
DT_bal = from_wei(datatoken.balanceOf(alice_wallet.address))
assert DT_bal >= num_consumes, f"Have just {DT_bal} datatokens"

# Alice sends datatokens to the service, to get access. This is the "consume".
for i in range(num_consumes):
    print(f"Consume #{i+1}/{num_consumes}...")
    ocean.assets.pay_for_access_service(asset, alice_wallet)
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
bal_before = from_wei(OCEAN.balanceOf(alice_wallet.address))
ocean.ve_fee_distributor.claim({"from": alice_wallet})
bal_after = from_wei(OCEAN.balanceOf(alice_wallet.address))
print(f"Just claimed {bal_after-bal_before} OCEAN rewards") 
```

## 7. Repeat steps 1-6, for Eth mainnet

We leave this as an exercise to the reader:)

Here's a hint to get started: initial setup is like the [simple-remote flow](simple-remote.md).

Happy Data Farming!

