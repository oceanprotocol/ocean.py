# Quickstart: Data Farming & Wash Consume Flow

This README shows how to do steps in Ocean Data Farming (DF), where you curate data assets to earn rewards. It also helps to democratize "wash consume" until it becomes unprofitable.

The latest release of ocean.py makes it very easy for us to interact with datatokens, the marketplace, veOCEAN, and DF. With it we’re able to easily play with the Ocean Protocol stack, use veOCEAN, and maybe even turn a profit (for now) by wash consuming and gaining reward from DF.

DF runs weekly, starting & ending on Thursdays @ midnight GMT. During this period the market is sampled, and all data assets are measured for `Data Consume Volume (DCV)` & `veOCEAN Allocated`. For each week, this is sampled 50 times to obtain an average, and to distribute Active Rewards for this period of participation.

"Wash Consuming" is when the publisher fake-consumes data to drive DCV to get more rewards. Not healthy for the ecosystem long-term. Good news: if consume fee > weekly rewards, then wash consume becomes unprofitable. DF is set up to make this happen by DF29 (if not sooner). [Details](https://twitter.com/trentmc0/status/1587527525529358336).

In the meantime, this README helps level the playing field around Wash Consume. 

This code should not be used on a live network. By reading and following any of these actions, you absolve others of any injury and are solely responsible for your actions.

Here are the steps:
1. Basic Setup, Ganache, and Python
2. Setup OCEAN and veOCEAN
3. Lock OCEAN for veOCEAN
4. Publish Dataset & FRE
5. Allocate veOCEAN to DataNFT
6. Fake-Consume data
7. Profit? Mainnet? What's next?

Let's go through each step.


## 1. Basic Setup, Ganache, and Python

Just like other READMEs.md in this repo, you need to complete a set of steps to get your basic setup working.

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python, including `ocean` and `alice_wallet`

At the end of it, you should be inside a Python console, with the ocean.py library talking to Ganache, and Alice's wallet available to use.


## 2. Setup OCEAN and veOCEAN

In order for us to use the Ocean marketplace and to play with Data Farming, we’re going to need some OCEAN and veOCEAN. Because we’re working in a development environment we start by minting OCEAN.

We'll use these a lot. So import once, here.

In the same Python console:
```python
# Set factory envvar. Stay in Python to retain state from before.
import os
os.environ['FACTORY_DEPLOYER_PRIVATE_KEY'] = '0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58'
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config) #Alice gets some
the
OCEAN = ocean.OCEAN_token
veOCEAN = ocean.ve_ocean

#helper functions
def to_wei(amt_eth) -> int:
    return int(amt_eth * 1e18)

def from_wei(amt_wei: int) -> float:
    return float(amt_wei / 1e18)
```


## 3. Lock OCEAN for veOCEAN

OCEAN is used to create datatokens, buy datatokens, reward participants, and obtain veOCEAN. veOCEAN is used to determine how rewards are distributed across the protocol, including via Data Farming. [This is](https://blog.oceanprotocol.com/introducing-veocean-c5f416c1f9a0) a great blog post to further comprehend veOCEAN.

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

# This is how much OCEAN to lock into veOCEAN. It can be small if you're
# the only staker on your asset. If others stake on your asset, your
# rewards are pro-rate compared to others' stake in your asset.
amt_OCEAN_lock = 100.0

#we're now at the beginning of the week. So, lock
OCEAN.approve(veOCEAN.address, to_wei(amt_OCEAN_lock), {"from" : alice_wallet})
veOCEAN.withdraw({"from": alice_wallet}) #withdraw old tokens first
veOCEAN.create_lock(to_wei(amt_OCEAN_lock), t2, {"from": alice_wallet})
```


## 4. Publish Dataset, FRE & DCV

If you have followed other README.mds, you might already be familiar with publishing a dataset via the Fixed Rate Exchange (FRE). We're going to follow this pattern here in order to explain DF.

**DF Key Concept #1:** Data Consume Volume (DCV).

Every week, you can earn Active Rewards for the following actions:
1. Locking Ocean to receive veOCEAN.
2. Allocating veOCEAN to a DataNFT.
3. Having datatokens associated with that DataNFT consumed.

So, if we can create our own dataset, point veOCEAN to it, and then consume from it, we can game DF.

There are two things to know:
1. Your asset DCV = datatoken_price_OCEAN * num_consumes.
1. Your assets rewards are pro-rata = your_asset_DCV / other_assets_DCV.

**Intuition #1:** The more the item costs, and the more it's consumed, the better it is for us. In the real world, Alice still needs to pay for fees.

**Intuition #2:** In the real world, Alice still needs to pay for fees.

Knowing all of this, create Alice's data asset that will be consumed, then put 3 of it on the market with a cost of 100.0 OCEAN each.

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
# On your asset, your DCV = datatoken_price_OCEAN * num_consumes.
# Your asset gets rewards pro-rata for its DCV compared to other assets' DCVs. 
datatoken_price_OCEAN = 100.0
num_consumes = 3

#create data asset
(data_NFT, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet, wait_for_aqua=False)
print(f"Just published asset, with data_NFT.address={data_NFT.address}")

# create fixed-rate exchange (FRE)
from web3 import Web3
exchange_id = ocean.create_fixed_rate(
    datatoken=datatoken,
    base_token=OCEAN,
    amount=to_wei(num_consumes),
    fixed_rate=to_wei(datatoken_price_OCEAN),
    from_wallet=alice_wallet,
)
```


## 5. Allocate veOCEAN to DataNFT

Now that we have our asset available to be purchased, we can try to game DF a little.

**DF Key Concept #2:** veOCEAN Allocated (Round Allocation).

To keep it simple we’re going to allocate 100% of Alice's veOCEAN to the data_NFT from the Branin dataset that we’re going to wash trade.

**Intuition #3:** DCV is multiplied by all veOCEAN allocated to it. So the more users are allocating veOCEAN to the same asset, the more dilluted the rewards will be.

In the same Python console:
```python
amt_allocate = 10000 #total allocation must be <= 10000 (100.00% (2 decimals) represented as an integer)
ocean.ve_allocate.setAllocation(amt_allocate, data_NFT.address, chain.id, {"from": alice_wallet})
```


## 6. Fake-Consume data

This step shows how to fake-consume. 

Alice is going to consume her own data and receive most of her money back. In the real world, Alice still needs to pay for fees.

In the same Python console:
```python
# Alice buys datatokens from herself
amt_pay = datatoken_price_OCEAN * num_consumes
OCEAN_bal = from_wei(OCEAN.balanceOf(alice_wallet.address))
assert OCEAN_bal >= amt_pay, f"Have just {OCEAN_bal} OCEAN"
OCEAN.approve(ocean.fixed_rate_exchange.address, to_wei(OCEAN_bal), {"from": alice_wallet})
fees_info = ocean.fixed_rate_exchange.get_fees_info(exchange_id)
for i in range(num_consumes):
    print(f"Purchase #{i+1}/{num_consumes}...")
    tx = ocean.fixed_rate_exchange.buyDT(
        exchange_id,
        to_wei(num_consumes), # datatokenAmount
        to_wei(OCEAN_bal),    # maxBaseTokenAmount
        fees_info[1], # consumeMarketAddress
        fees_info[0], # consumeMarketSwapFeeAmount
        {"from": alice_wallet},
    )
    assert tx, "buying datatokens failed"
DT_bal = from_wei(datatoken.balanceOf(alice_wallet.address))
assert DT_bal >= num_consumes, f"Have just {DT_bal} datatokens"

# Alice sends datatokens to the service, to get access. This is the "consume".
for i in range(num_consumes):
    print(f"Consume #{i+1}/{num_consumes}...")
    ocean.assets.pay_for_access_service(asset, alice_wallet)
    #don't need to call e.g. ocean.assets.download_asset() since wash-consuming
```


## 7. Profit? Mainnet? What's next?

We leave this as an exercise to the reader :)

Hint #1: Repeat steps 1-6 but use the initial setup of [simple-remote flow](simple-remote.md).

Hint #2: If Data Farming samples the week 50 times, how can you best capture DCV & veOCEAN allocated throughout the whole round?

We have now simulated wash-trading and manipulating of DF. Because Alice participated in DF by using her veOCEAN and helped to curate good datasets (her own dataNFT) she should receive some rewards.

Theoretically, you might be able to replicate this on ETH Mainnet and profit.

As outlined above when describing the evolution of Data Farming, the parameters and mechanisms are changing. Any edge available from this will come to an end.

This is definitely not financial advice.

Happy Data Farming!