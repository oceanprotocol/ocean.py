import brownie
import enforce
import pytest
import sys

from ocean_lib.spool_py import SFactory, SPool, BToken
from ocean_lib.ocean import util
from ocean_lib.ocean.util import fromBase18, toBase18
from ocean_lib.web3_internal.account import Account

HUGEINT = 2**255

def test_notokens_basic(OCEAN_address,
                        alice_context, alice_address, bob_context):
    pool = _deploySPool(alice_context)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens() #pool's not finalized
    assert pool.getSwapFee_base() == toBase18(1e-6)
    assert pool.getController() == alice_address
    assert str(pool)
    
    with pytest.raises(Exception): 
        pool.finalize() #can't finalize if no tokens

def test_setSwapFee_works(alice_context):
    pool = _deploySPool(alice_context)
    pool.setSwapFee(toBase18(0.011))
    assert fromBase18(pool.getSwapFee_base()) == 0.011
    
def test_setSwapFee_fails(alice_address, alice_context, bob_context):
    pool_address = SFactory.SFactory(alice_context).newSPool(alice_address)
    alice_pool = SPool.SPool(alice_context, pool_address)
    bob_pool = SPool.SPool(bob_context, pool_address)
    with pytest.raises(Exception):
        bob_pool.setSwapFee(toBase18(0.011)) #not ok, bob isn't controller
    alice_pool.setController(bob_context.address)
    bob_pool.setSwapFee(toBase18(0.011)) #ok now

def test_setController(alice_context, alice_address,
                       bob_context, bob_address):
    pool = _deploySPool(alice_context)
    pool.setController(bob_address)
    assert pool.getController() == bob_address
    bob_pool = SPool.SPool(bob_context, pool.address)
    bob_pool.setController(alice_address)
    assert pool.getController() == alice_address

def test_setPublicSwap(alice_context):
    pool = _deploySPool(alice_context)
    pool.setPublicSwap(True)
    assert pool.isPublicSwap()
    pool.setPublicSwap(False)
    assert not pool.isPublicSwap()

def test_2tokens_basic(alice_context, alice_address, alice_view, T1, T2):
    pool = _deploySPool(alice_context)
    assert T1.address != T2.address
    assert T1.address != pool.address

    with pytest.raises(Exception): #can't bind until we approve
        pool.bind(T1.address, toBase18(90.0), toBase18(9.0))

    #Bind two tokens to the pool
    T1.approve(pool.address, toBase18(90.0))
    T2.approve(pool.address, toBase18(10.0))

    allowance1 = fromBase18(T1.allowance_base(alice_address, pool.address))
    allowance2 = fromBase18(T2.allowance_base(alice_address, pool.address))
    assert allowance1 == 90.0
    assert allowance2 == 10.0
    print(f"T1 allowance from alice to pool: {allowance1}")
    print(f"T2 allowance from alice to pool: {allowance2}")
    import pdb; pdb.set_trace()
    
    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address, toBase18(90.0), toBase18(9.0))
    pool.bind(T2.address, toBase18(10.0), toBase18(1.0))
    assert pool.isBound(T1.address) and pool.isBound(T2.address)
    
    assert pool.getNumTokens() == 2
    assert pool.getCurrentTokens() == [T1.address, T2.address]

    assert pool.getDenormalizedWeight_base(T1.address) == toBase18(9.0)
    assert pool.getDenormalizedWeight_base(T2.address) == toBase18(1.0)
    assert pool.getTotalDenormalizedWeight_base() == toBase18(9.0+1.0)
    
    assert pool.getNormalizedWeight_base(T1.address) == toBase18(0.9)
    assert pool.getNormalizedWeight_base(T2.address) == toBase18(0.1)

    assert pool.getBalance_base(T1.address) == toBase18(90.0)
    assert pool.getBalance_base(T2.address) == toBase18(10.0)
    
    assert str(pool)

def test_unbind(alice_context, T1, T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,1.0,1.0,1.0,1.0)
    
    pool.unbind(T1.address)
    
    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert fromBase18(pool.getBalance_base(T2.address)) == 1.0

def test_finalize(alice_address, alice_context, T1, T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply_base() == 0
    assert pool.balanceOf_base(alice_address) == 0
    assert pool.allowance_base(alice_address, pool.address) == 0
    
    pool.finalize()
    
    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply_base() == toBase18(100.0)
    assert pool.balanceOf_base(alice_address) == toBase18(100.0)
    assert pool.allowance_base(alice_address, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]
    
def test_public_pool(alice_address, alice_context, bob_address, bob_context,
                     T1,T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)
    BPT = pool
        
    #alice give Bob some tokens
    alice_T1 = BToken.BToken(alice_context, T1.address)
    alice_T1.transfer(bob_address, toBase18(100.0))
    
    alice_T2 = BToken.BToken(alice_context, T2.address)
    alice_T2.transfer(bob_address, toBase18(100.0))

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == 0
    
    assert fromBase18(T1.balanceOf_base(bob_address)) == 100.0
    assert fromBase18(T2.balanceOf_base(bob_address)) == 100.0
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 0
    
    assert fromBase18(T1.balanceOf_base(pool.address))== 90.0
    assert fromBase18(T2.balanceOf_base(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0

    #finalize
    alice_pool = SPool.SPool(alice_context, pool.address)
    alice_pool.finalize()

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == 100.0 #new!
    
    assert fromBase18(T1.balanceOf_base(pool.address))== 90.0
    assert fromBase18(T2.balanceOf_base(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0

    #bob join pool. Wants 10 BPT
    bob_T1 = BToken.BToken(bob_context, T1.address)
    bob_T1.approve(pool.address, toBase18(100.0))
    
    bob_T2 = BToken.BToken(bob_context, T2.address)
    bob_T2.approve(pool.address, toBase18(100.0))
    
    bob_pool = SPool.SPool(bob_context, pool.address)
    bob_pool.joinPool(poolAmountOut_base=toBase18(10.0), #10 BPT
                      maxAmountsIn_base=[toBase18(100.0),toBase18(100.0)])

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address))== 100.0 
    
    assert fromBase18(T1.balanceOf_base(bob_address)) == (100.0-9.0)
    assert fromBase18(T2.balanceOf_base(bob_address)) == (100.0-1.0)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 10.0 
    
    assert fromBase18(T1.balanceOf_base(pool.address)) == (90.0+9.0)
    assert fromBase18(T2.balanceOf_base(pool.address)) == (10.0+1.0)
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0
    
    #bob sells 2 BPT
    # -this is where BLabs fee kicks in. But the fee is currently set to 0.
    bob_pool.exitPool(poolAmountIn_base=toBase18(2.0), 
                      minAmountsOut_base=[toBase18(0.0),toBase18(0.0)])
    assert fromBase18(T1.balanceOf_base(bob_address)) == 92.8
    assert fromBase18(T2.balanceOf_base(bob_address)) == 99.2
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 8.0 
    
    #bob buys 5 more BPT
    bob_pool.joinPool(poolAmountOut_base=toBase18(5.0), 
                      maxAmountsIn_base=[toBase18(90.0),toBase18(90.0)])
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 13.0
    
    #bob fully exits
    bob_pool.exitPool(poolAmountIn_base=toBase18(13.0), 
                      minAmountsOut_base=[toBase18(0.0),toBase18(0.0)])
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 0.0


def test_rebind_more_tokens(alice_context,T1,T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)
    
    #insufficient allowance
    with pytest.raises(Exception): 
        pool.rebind(T1.address, toBase18(120.0), toBase18(9.0))
        
    #sufficient allowance
    T1.approve(pool.address, toBase18(30.0))
    pool.rebind(T1.address, toBase18(120.0), toBase18(9.0))
    
def test_gulp(alice_context, T1):
    pool = _deploySPool(alice_context)
    
    #bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, toBase18(50.0))
    pool.bind(T1.address, toBase18(2.0), toBase18(50.0))

    #T1 is now pool's (a) ERC20 balance (b) _records[token].balance 
    assert T1.balanceOf_base(pool.address) == toBase18(2.0) #ERC20 balance
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, toBase18(5.0))
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20 bal
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address)
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20
    assert pool.getBalance_base(T1.address) == toBase18(2.0+5.0) #records[]

def test_spot_price(alice_context):
    (p, p_sans) = _spotPrices(alice_context, 1.0, 1.0, 1.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001

    (p, p_sans) = _spotPrices(alice_context, 90.0, 10.0, 9.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001
    
    (p, p_sans) = _spotPrices(alice_context, T1, T2, 1.0, 2.0, 1.0, 1.0)
    assert p_sans == 0.5
    assert round(p,8) == 0.5000005
    
    (p, p_sans) = _spotPrices(alice_context, T1, T2, 2.0, 1.0, 1.0, 1.0)
    assert p_sans == 2.0
    assert round(p,8) == 2.000002

    (p, p_sans) = _spotPrices(alice_context, T1, T2, 9.0, 10.0, 9.0, 1.0)
    assert p_sans == 0.1
    assert round(p,8) == 0.1000001

@enforce.runtime_validation
def _spotPrices(c: util.Context, T1:BToken.BToken, T2:BToken.BToken,
                bal1:float, bal2:float, w1:float, w2:float):
    pool = _createPoolWith2Tokens(c, T1, T2, bal1, bal2, w1, w2)
    a1, a2 = T1.address, T2.address
    return (fromBase18(pool.getSpotPrice_base(a1, a2)),
            fromBase18(pool.getSpotPriceSansFee_base(a1, a2))) 
    
def test_joinSwapExternAmountIn(alice_address, alice_context, T1, T2): 
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0, 9.0,1.0)
    T1.approve(pool.address, toBase18(100.0))

    #pool's not public
    with pytest.raises(Exception): 
        pool.swapExactAmountOut(
                tokenIn_address = T1.address,
                maxAmountIn_base = toBase18(100.0),
                tokenOut_address = T2.address,
                tokenAmountOut_base = toBase18(10.0),
                maxPrice_base = HUGEINT)

    #pool's public
    pool.setPublicSwap(True)
    pool.swapExactAmountOut(
            tokenIn_address = T1.address,
            maxAmountIn_base = toBase18(100.0),
            tokenOut_address = T2.address,
            tokenAmountOut_base = toBase18(1.0),
            maxPrice_base = HUGEINT)
    assert 908.94 <= fromBase18(T1.balanceOf_base(alice_address)) <= 908.95
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0 - 9.0)
    
def test_joinswapPoolAmountOut(alice_address, alice_context, T1, T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize()
    T1.approve(pool.address, toBase18(90.0))
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.joinswapPoolAmountOut(
            tokenIn_address = T1.address,
            poolAmountOut_base = toBase18(10.0), #BPT wanted
            maxAmountIn_base = toBase18(90.0))  #max T1 to spend
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 - 90.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 + 10.0)

def test_exitswapPoolAmountIn(alice_address, alice_context, T1, T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize()
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapPoolAmountIn(
            tokenOut_address = T1.address,
            poolAmountIn_base = toBase18(10.0), #BPT spent
            minAmountOut_base = toBase18(1.0)) #min T1 wanted
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 + 1.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 - 10.0)

def test_exitswapExternAmountOut(alice_address, alice_context, T1, T2):
    pool = _createPoolWith2Tokens(alice_context,T1,T2,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize()
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapExternAmountOut(
            tokenOut_address = T1.address,
            tokenAmountOut_base = toBase18(2.0), #T1 wanted
            maxPoolAmountIn_base = toBase18(10.0)) #max BPT spent
    assert fromBase18(T1.balanceOf_base(alice_address)) == (910.0 + 2.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) >= (100.0 - 10.0)

def test_calcSpotPrice_base(alice_address, alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcSpotPrice_base(
        tokenBalanceIn_base = toBase18(10.0),
        tokenWeightIn_base = toBase18(1.0),
        tokenBalanceOut_base = toBase18(11.0),
        tokenWeightOut_base = toBase18(1.0),
        swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.909

def test_calcOutGivenIn_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcOutGivenIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountIn_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.918

def test_calcInGivenOut_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcInGivenOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut_base = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountOut_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.099

def test_calcPoolOutGivenSingleIn_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcPoolOutGivenSingleIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            tokenAmountIn_base = toBase18(0.1),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.599    

def test_calcSingleInGivenPoolOut_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcSingleInGivenPoolOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountOut_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.736

def test_calcSingleOutGivenPoolIn_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcSingleOutGivenPoolIn_base(
            tokenBalanceOut_base = toBase18(10.0),
            tokenWeightOut_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountIn_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.597

def test_calcPoolInGivenSingleOut_base(alice_context):
    pool = _deploySPool(alice_context)
    x = pool.calcPoolInGivenSingleOut(
            tokenBalanceOut_base = toBase18(1000.0),
            tokenWeightOut_base = toBase18(5.0),
            poolSupply_base = toBase18(100.0),
            totalWeight_base = toBase18(10.0),
            tokenAmountOut_base = toBase18(0.1),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.005

@enforce.runtime_validation
def _getPoolWith2Tokens(c:util.Context,
                        pool_address:str,
                        T1_address:str, T2_address:str):
    """Create objects pointing to pre-existing pool and tokens,
    from the supplied context / view """
    T1 = BToken.BToken(c, T1_address)
    T2 = BToken.BToken(c, T2_address)
    pool = SPool.SPool(c, pool_address)
    return (pool, T1, T2)

@enforce.runtime_validation
def _createPoolWith2Tokens(c: util.Context,
                           T1: BToken.BToken, T2: BToken.BToken,
                           bal1:float, bal2:float, w1:float, w2:float):
    pool = _deploySPool(c)
    
    T1.approve(pool.address, toBase18(bal1))
    T2.approve(pool.address, toBase18(bal2))

    pool.bind(T1.address, toBase18(bal1), toBase18(w1))
    pool.bind(T2.address, toBase18(bal2), toBase18(w2))

    return (pool, T1, T2)

@enforce.runtime_validation
def _deploySPool(c: util.Context) -> SPool.SPool:
    address = SFactory.SFactory(c).newSPool(c.address)
    return SPool.SPool(c, address)
