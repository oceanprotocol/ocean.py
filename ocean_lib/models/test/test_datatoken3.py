"""
Summary: 
This file is an implementation using OCEAN staking, and DTs. 
Runs end-to-end.

Protototype 3. https://github.com/oceanprotocol/predictoor-pm/issues/10

Previous prototypes:
- Prot 1: OCEAN staking, no DT. https://github.com/oceanprotocol/predictoor/blob/main/tests/test_predictoor.py
- Prot 2: veOCEAN staking, DT. https://github.com/oceanprotocol/predictoor/blob/main/tests/test_datatoken_approach.py

Q: how to reconcile DNFT/DT with "access control (incl onchain)"?
SubQ: How to have a *feed* where DT owner doesn't need to claim each time?
A: new datatoken template (#3) for predictoor.sol functionality

How datatoken (DT) gives predictoor.sol functionality:
- DT adds methods: submit predictions, get agg predval
  - Staking = as part of submitting predictions
- DT or exchange adds methods: release(). TBD.
- DT revises access control: all onchain. DT holds list of who's claimed &when
  - *Not* the usual ocean_assets.py::pay_for_access_service() because that's highly dependent on off-chain Provider & passing in DDOs. Don't need or want.
- DT maintains existing functionality: DT custody, allow/transfer, buy, fees..
What about Data NFT (DNFT) ?
- We don't need a new DNFT template (!)
- Leverages existing ERC71 functionality: "owner", transfer(), ..
- Leverages existing Ocean functionality: create_datatoken() // create_ERC20()
py interface is part of ocean.py (!)
Prototype by branching "contracts" and "ocean.py" repos

Q: how to reconcile DNFT/DT with "distribute $ from feed?
-Idea 1: leverage the data NFT or DT. Perhaps with a splitter-style contract below. 
-Idea 2: have a new exchange that splits things up when pmts accepted
-Let's explore the answer to this, and the rest, via prototyping.

************
Remaining challenges:
- privacy for submitted predvals, agg predval, when computing agg predval. See Product Design GDoc. 
"""
import os
    
import brownie
from brownie.network import accounts
import pytest
from pytest import approx
    
from ocean_lib.example_config import get_config_dict
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.util import from_wei, to_wei

accounts = brownie.network.accounts
chain = brownie.network.chain

def test_main_py():
    _test_main(use_py=True)

@pytest.mark.skip(reason="turn this on once .sol version is built")
def test_main_sol():
    _test_main(use_py=False)
    
def _test_main(use_py):

    #======
    #SETUP SYSTEM
    connect_to_network("development")
    config = get_config_dict("development")
    ocean = Ocean(config)
    OCEAN = ocean.OCEAN_token

    #convenience functions to get OCEAN balance & allowance, ETH balance
    c = ConvClass(OCEAN)
    OCEAN_bal = c.fromWei_balanceOf
    OCEAN_approved = c.fromWei_approved
    def ETH_bal(acct):
        return from_wei(acct.balance())

    # Ensure that users have OCEAN and ETH as needed
    # -Note: Barge minted fake OCEAN and gave it to TEST_PRIVATE_KEY{1,2}
    opf = accounts.add(os.getenv("TEST_PRIVATE_KEY1"))
    predictoor1 = accounts.add(os.getenv("TEST_PRIVATE_KEY2"))
    predictoor2 = accounts.add()
    trader = accounts.add()
    rando = accounts.add()
    accts = [opf, predictoor1, predictoor2, trader, rando]

    print("n\Balances before moving funds:")
    for i, acct in enumerate(accts):
        print(f"acct {i}: {ETH_bal(acct)} ETH, {OCEAN_bal(acct)} OCEAN")

    print("\nMove funds...")
    for acct in [predictoor2, trader, rando]:
        opf.transfer(acct, to_wei(100.0))
        OCEAN.transfer(acct, to_wei(100.0), {"from": opf})

    print("\nBalances after moving funds:")
    for i, acct in enumerate(accts):
        print(f"acct {i}: {ETH_bal(acct)} ETH, {OCEAN_bal(acct)} OCEAN")

    #check if enough funds
    for i, acct in enumerate(accts):
        assert ETH_bal(acct) > 0, f"acct {i} needs ETH"
        assert OCEAN_bal(acct), f"acct {i} needs OCEAN"

    #======================================================================
    #SETUP CONTRACTS

    min_blocks_ahead = 20 # Pred'ns must be >= this # blocks ahead
    min_predns_for_payout = 100 # Predictoor must have >= this # predn's to get paid
    num_blocks_subscription = 86400 / 10 # 1 day

    #can reuse existing DNFT template
    data_nft = ocean.data_nft_factory.create(
        {"from": opf}, "Data NFT 1", "DNFT1", #and any other DataNFTArguments
    )

    #new DT template with Predictoor functionality
    DT = data_nft.create_datatoken(
        {"from": opf}, name="Datatoken 1", symbol="DT1",
        template_index=3,
        min_blocks_ahead=min_blocks_ahead,
        min_predns_for_payout=min_predns_for_payout,
        num_blocks_subscription=num_blocks_subscription,
        #and any other DatatokenArguments
    )

    #post 100 DTs for sale
    n_DTs = 100.0
    DT.mint(opf, to_wei(n_DTs), {"from": opf})

    DT_price = 10.0 #denominated in OCEAN
    exchange = DT.create_exchange(
        {"from": opf}, to_wei(pmt_amount), OCEAN.address)
    DT.approve(exchange.address, to_wei(n_DTs), {"from": opf})

    predictoors = [predictoor1, predictoor2]

    #======================================================================
    #TRADER BUYS SUBSCRIPTION TO AGG PREDVALS (do every 24h)

    # trader buys 1 DT with OCEAN
    OCEAN_needed = exchange.BT_needed(to_wei(1), consume_market_fee=0)
    OCEAN.approve(exchange.address, to_wei(OCEAN_needed), {"from": trader})
    exchange.buy_DT(to_wei(1), {"from": trader}) #spends OCEAN

    # trader starts subscription. Good for 24h.
    # -"start_subscription" is like pay_for_access_service, but w/o DDO
    DT.approve(DT, to_wei(1), {"from": trader})
    DT.start_subscription({"from": trader}) # good for next 24h (or 1h, 7d, ..)

    #======================================================================
    #PREDICTOORS STAKE & SUBMIT PREDVALS (do every 5min)
    predval1, stake1 = 1500, 10.0    
    predval2, stake2 = 1600, 20.0

    OCEAN.approve(DT, to_wei(stake1), predictoor1)
    OCEAN.approve(DT, to_wei(stake2), predictoor2)
    assert OCEAN_approved(predictoor1, DT) == stake1 #new, ready to use
    assert OCEAN_approved(predictoor2, DT) == stake2 #""

    DT.submit_predval(to_wei(predval1), to_wei(stake1), predict_blocknum, {"from":predictoor1})
    DT.submit_predval(to_wei(predval1), to_wei(stake2), predict_blocknum, {"from":predictoor2})

    #test
    assert OCEAN_bal(DT) == (stake1 + stake2)  #just got new stake
    assert OCEAN_bal(predictoor1) == (initbal - stake1) #just staked
    assert OCEAN_bal(predictoor2) == (initbal - stake2) #""
    assert OCEAN_approved(predictoor1, DT) == 0.0 #just used up
    assert OCEAN_approved(predictoor2, DT) == 0.0 #""

    #======================================================================
    #TRADER GETS AGG PREDVAL (do every 5min)

    # trader gets prediction itself
    # -a tx isn't needed, therefore Solidity can return a value directly
    # -"get_agg_predval" is like ocean.assets.download_asset //
    #  asset_downloader.download_asset_files() except there's no downloading,
    #  rather it simply gives the agg_predval. (To generalize: reveals secret)
    agg_predval_wei = DT.get_agg_predval(predict_blocknum)
    
    #======================================================================
    #TIME PASSES - enough such that predict_blocknum has passed
    chain.mine(min_blocks_ahead + 10) # pass enough time (blocks) so that  pass

    #======================================================================
    #OWNER SUBMITS TRUE VALUE. This will update predictoors' claimable amts
    trueval = 1612.0
    DT.submit_trueval(to_wei(trueval), predict_blocknum, {"from":opf})
    
    #======================================================================
    #TIME PASSES - enough for predictoors to get claims

    # FIXME - we'll need to do 'min_predns_for_payout' loops through this
    #   step and and several prev steps, for predictoors to actually get paid
    chain.mine(int(1.2 * min_blocks_ahead * min_predns_for_payout))

    #======================================================================
    #PREDICTOORS & OPF COLLECT SALES REVENUE

    # Any rando can call release(). Will update amt allowed
    # OR!!! this is where exchange object comes in!!
    DT.release({"from": rando})

    # Each actor collects its cut of DT sales
    for acct in predictoors + [opf]:
        amt = getallow(DT, acct)
        OCEAN.transferFrom(DT.address, acct.address, to_wei(amt), {"from": acct})


class ConvClass: 
    def __init__(self, token):
        self.token = token

    def fromWei_balanceOf(self, obj) -> float:
        return from_wei(self.token.balanceOf(obj.address))

    def fromWei_approved(self, obj1, obj2) -> float:
        return from_wei(self.token.allowance(obj1.address, obj2.address))

def _cur_blocknum():
    return chain[-1].number
        
def _predictoor_contract(
        use_py:bool,
        min_blocks_ahead:int,
        num_blocks_before_release:int,
        pmt_token,
        DT_price_wei:int,
        tx_dict:dict,
        contract_account):

    if use_py: # python version
        return PyPredictoorContract(
            min_blocks_ahead,
            num_blocks_before_release,
            pmt_token,
            DT_price_wei,
            tx_dict,
            contract_account)

    else: # solidity version
        assert contract_account is None
        return B.Predictoor.deploy() #FIXME: put in args when ready to do .sol

    
def _deployOCEAN(owner):
    total_supply = 10e3
    OCEAN = B.Simpletoken.deploy(
        "OCEAN", "OCEAN", 18, to_wei(total_supply), {"from": owner})
    bal_opf = from_wei(OCEAN.balanceOf(opf))
    assert bal_opf == 10e3, "expected deployer to get all OCEAN"
    return OCEAN
    
