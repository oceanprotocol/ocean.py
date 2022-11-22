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
# OCEAN
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config) #Alice gets some
OCEAN = ocean.OCEAN_token

# veOCEAN
from ocean_lib.models.ve_ocean import VeOcean
from ocean_lib.models.ve_allocate import VeAllocate
from ocean_lib.models.ve_fee_distributor import VeFeeDistributor
from ocean_lib.ocean.util import get_address_of_type
veOCEAN = VeOcean(config, get_address_of_type(config, "veOCEAN"))
ve_allocate = VeAllocate(config, get_address_of_type(config, "veAllocate"))
ve_fee_distributor = VeFeeDistributor(config, get_address_of_type(config, "veFeeDistributor"))

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
OCEAN.approve(veOCEAN.address, to_wei(amt_OCEAN_lock), alice_wallet)
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
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
fixedPrice = FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))
datatoken.approve(fixedPrice.address, to_wei(num_consumes), alice_wallet)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
txid = datatoken.create_fixed_rate(
    fixed_price_address = fixedPrice.address,
    base_token_address = OCEAN.address,
    owner = alice_wallet.address,
    publish_market_swap_fee_collector = alice_wallet.address,
    allowed_swapper = ZERO_ADDRESS,
    base_token_decimals = OCEAN.decimals(),
    datatoken_decimals = datatoken.decimals(),
    fixed_rate = to_wei(datatoken_price_OCEAN),
    publish_market_swap_fee_amount = 0,
    with_mint = 1,
    from_wallet = alice_wallet
)
from brownie.network.transaction import TransactionReceipt
tx = TransactionReceipt(txid)
exchange_id = tx.events["NewFixedRate"]["exchangeId"]
```


## 4. Stake on dataset

To stake, you allocate veOCEAN to dataset. In the same Python console:
```python
amt_allocate = 100 #total allocation must be <= 10000 (wei)
ve_allocate.setAllocation(amt_allocate, data_NFT.address, chain.id, {"from": alice_wallet})
```

## 5. Fake-consume data

"Wash consuming" is when the publisher fake-consumes data to drive data consume volume (DCV) to get more rewards. Not healthy for the ecosystem long-term. Good news: if consume fee > weekly rewards, then wash consume becomes unprofitable. DF is set up to make this happen by DF29 (if not sooner). [Details](https://twitter.com/trentmc0/status/1587527525529358336).

In the meantime, this README helps level the playing field around wash consume. This step shows how to do fake-consume.

```python
# Alice buys datatokens from herself
amt_pay = datatoken_price_OCEAN * num_consumes
OCEAN_bal = from_wei(OCEAN.balanceOf(alice_wallet.address))
assert OCEAN_bal >= amt_pay, f"Have just {OCEAN_bal} OCEAN"
OCEAN.approve(fixedPrice.address, to_wei(OCEAN_bal), alice_wallet)
fees_info = fixedPrice.get_fees_info(exchange_id)
for i in range(num_consumes):
    print(f"Purchase #{i+1}/{num_consumes}...")
    txid = fixedPrice.buy_dt(
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
ve_fee_distributor.claim({"from": alice_wallet})
bal_after = from_wei(OCEAN.balanceOf(alice_wallet.address))
print(f"Just claimed {bal_after-bal_before} OCEAN rewards") 
```

## 7. Repeat steps 1-6, for Eth mainnet

FIXME

