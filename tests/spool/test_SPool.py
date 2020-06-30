import brownie
import enforce
import pytest
import sys

from ocean_lib.spool_py import SFactory, SPool, BToken
from ocean_lib.ocean import util
from ocean_lib.ocean.util import fromBase18, toBase18
from ocean_lib.web3_internal.account import Account
from ocean_lib.web3_internal.wallet import Wallet

HUGEINT = 2**255

def test_notokens_basic(OCEAN_address, network, alice_wallet, alice_address):
    pool = _deploySPool(network, alice_wallet)

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

def test_setSwapFee_works(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    pool.setSwapFee(toBase18(0.011), from_wallet=alice_wallet)
    assert fromBase18(pool.getSwapFee_base()) == 0.011
    
def test_setSwapFee_fails(network,
                          alice_wallet, alice_address,
                          bob_wallet, bob_address):
    web3 = alice_wallet.web3
    factory = SFactory.SFactory(web3, _sfactory_address(network))
    pool_address = factory.newSPool(alice_wallet)
    pool = SPool.SPool(web3, pool_address)
    with pytest.raises(Exception):
        pool.setSwapFee(toBase18(0.011), from_wallet=bob_wallet) #not ok, bob isn't controller
    pool.setController(bob_address, from_wallet=alice_wallet)
    pool.setSwapFee(toBase18(0.011), from_wallet=bob_wallet) #ok now

def test_setController(network, alice_wallet, alice_address,
                       bob_wallet, bob_address):
    web3 = alice_wallet.web3
    pool = _deploySPool(network, alice_wallet)
    pool.setController(bob_address, from_wallet=alice_wallet)
    assert pool.getController() == bob_address
    
    pool.setController(alice_address, from_wallet=bob_wallet)
    assert pool.getController() == alice_address

def test_setPublicSwap(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    assert pool.isPublicSwap()
    pool.setPublicSwap(False, from_wallet=alice_wallet)
    assert not pool.isPublicSwap()

def test_2tokens_basic(network, T1, T2,
                       alice_wallet, alice_address, alice_view):
    pool = _deploySPool(network, alice_wallet)
    assert T1.address != T2.address
    assert T1.address != pool.address

    assert fromBase18(T1.balanceOf_base(alice_address)) >= 90.0
    bal2 = fromBase18(T2.balanceOf_base(alice_address)) >= 10.0

    with pytest.raises(Exception): #can't bind until we approve
        pool.bind(T1.address, toBase18(90.0), toBase18(9.0))

    #Bind two tokens to the pool
    T1.approve(pool.address, toBase18(90.0), from_wallet=alice_wallet)
    T2.approve(pool.address, toBase18(10.0), from_wallet=alice_wallet)

    assert fromBase18(T1.allowance_base(alice_address, pool.address)) == 90.0
    assert fromBase18(T2.allowance_base(alice_address, pool.address)) == 10.0
    
    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address,toBase18(90.0),toBase18(9.0),from_wallet=alice_wallet)
    pool.bind(T2.address,toBase18(10.0),toBase18(1.0),from_wallet=alice_wallet)
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

def test_unbind(network, T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,1.0,1.0,1.0,1.0)
    
    pool.unbind(T1.address, from_wallet=alice_wallet)
    
    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert fromBase18(pool.getBalance_base(T2.address)) == 1.0

def test_finalize(network, T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply_base() == 0
    assert pool.balanceOf_base(alice_address) == 0
    assert pool.allowance_base(alice_address, pool.address) == 0
    
    pool.finalize(from_wallet=alice_wallet)
    
    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply_base() == toBase18(100.0)
    assert pool.balanceOf_base(alice_address) == toBase18(100.0)
    assert pool.allowance_base(alice_address, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]
    
def test_public_pool(network, T1, T2,
                     alice_address, alice_wallet,
                     bob_address, bob_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool
    web3 = alice_wallet.web3
        
    #alice give Bob some tokens
    T1.transfer(bob_address, toBase18(100.0), from_wallet=alice_wallet)
    T2.transfer(bob_address, toBase18(100.0), from_wallet=alice_wallet)

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
    pool = SPool.SPool(web3, pool.address)
    pool.finalize(from_wallet=alice_wallet)

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == 100.0 #new!
    
    assert fromBase18(T1.balanceOf_base(pool.address))== 90.0
    assert fromBase18(T2.balanceOf_base(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0

    #bob join pool. Wants 10 BPT
    T1.approve(pool.address, toBase18(100.0), from_wallet=bob_wallet)
    T2.approve(pool.address, toBase18(100.0), from_wallet=bob_wallet)
    pool.joinPool(poolAmountOut_base=toBase18(10.0), #10 BPT
                  maxAmountsIn_base=[toBase18(100.0),toBase18(100.0)],
                  from_wallet=bob_wallet)

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
    pool.exitPool(poolAmountIn_base=toBase18(2.0), 
                  minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(T1.balanceOf_base(bob_address)) == 92.8
    assert fromBase18(T2.balanceOf_base(bob_address)) == 99.2
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 8.0 
    
    #bob buys 5 more BPT
    pool.joinPool(poolAmountOut_base=toBase18(5.0), 
                  maxAmountsIn_base=[toBase18(90.0),toBase18(90.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 13.0
    
    #bob fully exits
    pool.exitPool(poolAmountIn_base=toBase18(13.0), 
                  minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 0.0


def test_rebind_more_tokens(network, T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    
    #insufficient allowance
    with pytest.raises(Exception): 
        pool.rebind(T1.address, toBase18(120.0), toBase18(9.0),
                    from_wallet=alice_wallet)
        
    #sufficient allowance
    T1.approve(pool.address, toBase18(30.0),
               from_wallet=alice_wallet)
    pool.rebind(T1.address, toBase18(120.0), toBase18(9.0),
                from_wallet=alice_wallet)
    
def test_gulp(network, T1, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    
    #bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, toBase18(50.0), from_wallet=alice_wallet)
    pool.bind(T1.address, toBase18(2.0), toBase18(50.0),
              from_wallet=alice_wallet)

    #T1 is now pool's (a) ERC20 balance (b) _records[token].balance 
    assert T1.balanceOf_base(pool.address) == toBase18(2.0) #ERC20 balance
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, toBase18(5.0), from_wallet=alice_wallet)
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20 bal
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address, from_wallet=alice_wallet)
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20
    assert pool.getBalance_base(T1.address) == toBase18(2.0+5.0) #records[]

def test_spot_price(network, T1, T2, alice_wallet):
    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet,
                              1.0, 1.0, 1.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet,
                              90.0, 10.0, 9.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001
    
    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet,
                              1.0, 2.0, 1.0, 1.0)
    assert p_sans == 0.5
    assert round(p,8) == 0.5000005
    
    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet,
                              2.0, 1.0, 1.0, 1.0)
    assert p_sans == 2.0
    assert round(p,8) == 2.000002

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet,
                              9.0, 10.0, 9.0,1.0)
    assert p_sans == 0.1
    assert round(p,8) == 0.1000001

@enforce.runtime_validation
def _spotPrices(network: str,
                T1: BToken.BToken, T2: BToken.BToken,
                wallet: Wallet, 
                bal1:float, bal2:float, w1:float, w2:float):
    pool = _createPoolWith2Tokens(network,T1,T2,wallet, bal1, bal2, w1, w2)
    a1, a2 = T1.address, T2.address
    return (fromBase18(pool.getSpotPrice_base(a1, a2)),
            fromBase18(pool.getSpotPriceSansFee_base(a1, a2))) 
    
def test_joinSwapExternAmountIn(network, T1, T2, alice_wallet, alice_address): 
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    T1.approve(pool.address, toBase18(100.0), from_wallet=alice_wallet)

    #pool's not public
    with pytest.raises(Exception): 
        pool.swapExactAmountOut(
                tokenIn_address = T1.address,
                maxAmountIn_base = toBase18(100.0),
                tokenOut_address = T2.address,
                tokenAmountOut_base = toBase18(10.0),
                maxPrice_base = HUGEINT,
                from_wallet=alice_wallet)

    #pool's public
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    pool.swapExactAmountOut(
            tokenIn_address = T1.address,
            maxAmountIn_base = toBase18(100.0),
            tokenOut_address = T2.address,
            tokenAmountOut_base = toBase18(1.0),
            maxPrice_base = HUGEINT,
            from_wallet=alice_wallet)
    assert 908.94 <= fromBase18(T1.balanceOf_base(alice_address)) <= 908.95
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0 - 9.0)
    
def test_joinswapPoolAmountOut(network, T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    T1.approve(pool.address, toBase18(90.0), from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.joinswapPoolAmountOut(
            tokenIn_address = T1.address,
            poolAmountOut_base = toBase18(10.0), #BPT wanted
            maxAmountIn_base = toBase18(90.0),  #max T1 to spend
            from_wallet=alice_wallet) 
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 - 90.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 + 10.0)

def test_exitswapPoolAmountIn(network, T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapPoolAmountIn(
            tokenOut_address = T1.address,
            poolAmountIn_base = toBase18(10.0), #BPT spent
            minAmountOut_base = toBase18(1.0),  #min T1 wanted
            from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 + 1.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 - 10.0)

def test_exitswapExternAmountOut(network, T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(network,T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapExternAmountOut(
            tokenOut_address = T1.address,
            tokenAmountOut_base = toBase18(2.0), #T1 wanted
            maxPoolAmountIn_base = toBase18(10.0), #max BPT spent 
            from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == (910.0 + 2.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) >= (100.0 - 10.0)

def test_calcSpotPrice_base(network, T1, T2, alice_address, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcSpotPrice_base(
        tokenBalanceIn_base = toBase18(10.0),
        tokenWeightIn_base = toBase18(1.0),
        tokenBalanceOut_base = toBase18(11.0),
        tokenWeightOut_base = toBase18(1.0),
        swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.909

def test_calcOutGivenIn_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcOutGivenIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountIn_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.918

def test_calcInGivenOut_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcInGivenOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut_base = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountOut_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.099

def test_calcPoolOutGivenSingleIn_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcPoolOutGivenSingleIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            tokenAmountIn_base = toBase18(0.1),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.599    

def test_calcSingleInGivenPoolOut_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcSingleInGivenPoolOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountOut_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.736

def test_calcSingleOutGivenPoolIn_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
    x = pool.calcSingleOutGivenPoolIn_base(
            tokenBalanceOut_base = toBase18(10.0),
            tokenWeightOut_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountIn_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.597

def test_calcPoolInGivenSingleOut_base(network, alice_wallet):
    pool = _deploySPool(network, alice_wallet)
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
def _createPoolWith2Tokens(network: str,
                           T1: BToken.BToken, T2: BToken.BToken,
                           wallet: Wallet, 
                           bal1:float, bal2:float, w1:float, w2:float):
    pool = _deploySPool(network, wallet)
    
    T1.approve(pool.address, toBase18(bal1), from_wallet=wallet)
    T2.approve(pool.address, toBase18(bal2), from_wallet=wallet)

    pool.bind(T1.address, toBase18(bal1), toBase18(w1), from_wallet=wallet)
    pool.bind(T2.address, toBase18(bal2), toBase18(w2), from_wallet=wallet)

    return pool

@enforce.runtime_validation
def _deploySPool(network: str, from_wallet: Wallet) -> SPool.SPool:
    web3 = from_wallet.web3
    factory_address = util.confFileValue(network, 'SFACTORY_ADDRESS')
    factory = SFactory.SFactory(web3, factory_address)
    pool_address = factory.newSPool(from_wallet=from_wallet)
    pool = SPool.SPool(web3, pool_address)
    return pool

@enforce.runtime_validation
def _sfactory_address(network: str) -> str:
    return util.confFileValue(network, 'SFACTORY_ADDRESS')
