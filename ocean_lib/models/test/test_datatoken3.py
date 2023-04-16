"""
Summary: 
This file is an implementation using OCEAN staking, and DTs. 
Runs end-to-end.

Protototype 3. https://github.com/oceanprotocol/predictoor-pm/issues/10

Previous prototypes:
- Prot 1: OCEAN staking, no DT. https://github.com/oceanprotocol/predictoor/blob/main/tests/test_predictoor.py
- Prot 2: veOCEAN staking, DT. https://github.com/oceanprotocol/predictoor/blob/main/tests/test_datatoken_approach.py

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

import brownie
import pytest
from pytest import approx

from util.base18 import from_wei, to_wei
from util.constants import BROWNIE_PROJECT as B
from util.predictoor import PyPredictoorContract

accounts = brownie.network.accounts
chain = brownie.network.chain
predictoor1, predictoor2, trader, opf, rando, contract_account = accounts[:6]

def test_init_py():
    _test_init(use_py=True)

@pytest.mark.skip(reason="turn this on once .sol version is built")
def test_init_sol():
    _test_init(use_py=False)

def _test_init(use_py):
    OCEAN = _deployOCEAN(opf)
    pe_contract = _predictoor_contract(
        use_py, 5, OCEAN, to_wei(100.1), {"from": opf}, contract_account)
    assert pe_contract.address == contract_account.address 
    assert pe_contract.min_blocks_ahead() == 5
    assert pe_contract.pmt_token().address == OCEAN.address
    assert from_wei(pe_contract.pmt_amt_wei()) == 100.1

def test_main_py():
    _test_main(use_py=True)

@pytest.mark.skip(reason="turn this on once .sol version is built")
def test_main_sol():
    _test_main(use_py=False)
    
def _test_main(use_py):
    #======================================================================
    #deploy OCEAN, give some to key users
    OCEAN = _deployOCEAN(opf)
    initbal = 1000.0
    OCEAN.transfer(predictoor1, to_wei(initbal), {"from": opf})
    OCEAN.transfer(predictoor2, to_wei(initbal), {"from": opf})
    OCEAN.transfer(trader, to_wei(initbal), {"from": opf})

    #convenience functions to get OCEAN balance & allowance
    c = ConvClass(OCEAN)
    getbal = c.fromWei_balanceOf
    getallow = c.fromWei_allowance
    approve = c.toWei_approve

    #======================================================================
    #deploy contract
    num_blocks_ahead = 20 # Pred'ns must be >= this # blocks ahead
    num_blocks_before_release = 100 # time til funds releasable
    pmt_amt = 100.0 # price
    pe_contract = _predictoor_contract(
        use_py = use_py,
        min_blocks_ahead = 5, # < num_blocks_head because we need txs to test
        num_blocks_before_release = num_blocks_before_release,
        pmt_token = OCEAN,
        pmt_amt_wei = to_wei(pmt_amt),
        tx_dict = {"from":opf},
        contract_account = contract_account
    )
    predict_blocknum =  _cur_blocknum() + num_blocks_ahead

    #======================================================================
    #predictoors submit predictions
    predval1, stake1 = 1500, 10.0    
    predval2, stake2 = 1600, 20.0

    approve(pe_contract, stake1, predictoor1)
    approve(pe_contract, stake2, predictoor2)
    assert getallow(predictoor1, pe_contract) == stake1 #new, ready to use
    assert getallow(predictoor2, pe_contract) == stake2 #""
    
    pe_contract.submit_predval(
        to_wei(predval1), to_wei(stake1), predict_blocknum,{"from":predictoor1})
    pe_contract.submit_predval(
        to_wei(predval2), to_wei(stake2), predict_blocknum,{"from":predictoor2})

    #test
    assert getbal(pe_contract) == (stake1 + stake2)  #just got new stake
    assert getbal(predictoor1) == (initbal - stake1) #just staked
    assert getbal(predictoor2) == (initbal - stake2) #""
    assert getallow(predictoor1, pe_contract) == 0.0 #just used up
    assert getallow(predictoor2, pe_contract) == 0.0 #""


    #======================================================================
    #trader gets aggregated prediction value, for a price
    assert getbal(trader) == initbal
    
    approve(pe_contract, pmt_amt, trader)
    assert getallow(trader, pe_contract) == pmt_amt #new
    
    agg_predval_wei = pe_contract.get_agg_predval(
        predict_blocknum, {"from": trader})
    assert agg_predval_wei is not None, "we expected predictions here"
    
    agg_predval = from_wei(agg_predval_wei)
    assert agg_predval == (10.0*1500 + 20.0*1600) / (10.0 + 20.0)

    #test
    assert getbal(pe_contract) == (stake1 + stake2 + pmt_amt) #just got pmt_amt
    assert getbal(predictoor1) == (initbal - stake1) #no change
    assert getbal(predictoor2) == (initbal - stake2) #""
    assert getbal(trader) == (initbal - pmt_amt)     #just spent pmt_amt
    
    assert getallow(predictoor1, pe_contract) == 0.0 #no change
    assert getallow(predictoor2, pe_contract) == 0.0 #"
    assert getallow(trader, pe_contract) == 0.0      #just used up

    
    #======================================================================
    #time passes
    chain.mine(num_blocks_ahead + 10) # pass enough time (blocks) so that  pass

    
    #======================================================================
    #owner submits true value. This will update predictoors' claimable amts
    trueval = 1612.0
    pe_contract.submit_trueval(
        to_wei(trueval), predict_blocknum, {"from":opf})

    #none of the balances or allowances should have changed. Must wait!
    assert getbal(pe_contract) == (stake1 + stake2 + pmt_amt) #no change
    assert getbal(predictoor1) == (initbal - stake1) #no change
    assert getbal(predictoor2) == (initbal - stake2) #""
    
    assert getallow(predictoor1, pe_contract) == 0.0 #no change
    assert getallow(predictoor2, pe_contract) == 0.0 #"
    assert getallow(trader, pe_contract) == 0.0      #"
    
    #======================================================================
    #let time pass, then release to update predictoors' claimable amts
    chain.mine(num_blocks_before_release)
    pe_contract.release({"from": rando})

    exp_pmt1 = 100.1 * 10.0/(10.0+20.0)
    exp_pmt2 = 100.1 * 20.0/(10.0+20.0)

    #test
    assert getbal(pe_contract) == (stake1 + stake2 + pmt_amt) #no change
    assert getbal(predictoor1) == (initbal - stake1) #no change
    assert getbal(predictoor2) == (initbal - stake2) #""

    assert getallow(pe_contract,predictoor1)==approx(exp_pmt1+stake1,rel=0.1)
    assert getallow(pe_contract,predictoor2)==approx(exp_pmt2+stake2,rel=0.1)


    #======================================================================
    #predictoors claim their $
    allow1 = getallow(pe_contract, predictoor1)
    allow2 = getallow(pe_contract, predictoor2)
    
    OCEAN.transferFrom(
        pe_contract.address, predictoor1.address, to_wei(allow1),
        {"from": predictoor1})
    OCEAN.transferFrom(
        pe_contract.address, predictoor2.address, to_wei(allow2),
        {"from": predictoor2})

    #test
    assert getbal(pe_contract) == approx(0.0)
    assert getbal(predictoor1) == \
        approx(initbal - stake1 + exp_pmt1 + stake1, rel=0.1) # pmt + stake back
    assert getbal(predictoor2) == \
        approx(initbal - stake2 + exp_pmt2 + stake2, rel=0.1) # pmt + stake back
    
    assert getallow(pe_contract, predictoor1) == approx(0.0) #just used up
    assert getallow(pe_contract, predictoor2) == approx(0.0) #""


class ConvClass: 
    def __init__(self, token):
        self.token = token

    def fromWei_balanceOf(self, obj) -> float:
        return from_wei(self.token.balanceOf(obj.address))

    def fromWei_allowance(self, obj1, obj2) -> float:
        return from_wei(self.token.allowance(obj1.address, obj2.address))

    def toWei_approve(self, to_obj, amt:float, from_obj) -> float:
        self.token.approve(to_obj.address, to_wei(amt), {"from":from_obj})

def _cur_blocknum():
    return chain[-1].number
        
def _predictoor_contract(
        use_py:bool,
        min_blocks_ahead:int,
        num_blocks_before_release:int,
        pmt_token,
        pmt_amt_wei:int,
        tx_dict:dict,
        contract_account):

    if use_py: # python version
        return PyPredictoorContract(
            min_blocks_ahead,
            num_blocks_before_release,
            pmt_token,
            pmt_amt_wei,
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
    
